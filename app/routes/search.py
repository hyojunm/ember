"""
Search & Transcription routes powered by Dedalus Labs SDK.

- POST /api/search      — semantic search over item embeddings
- POST /api/transcribe   — voice-to-text via Dedalus audio transcription
"""

import json
import math
import traceback
from pathlib import Path

from flask import Blueprint, request, jsonify
from sqlalchemy.orm import joinedload

from ..extensions import db, get_dedalus_client
from ..models import Item

bp = Blueprint('search', __name__)

EMBEDDING_MODEL = "openai/text-embedding-3-small"
TRANSCRIPTION_MODEL = "groq/whisper-large-v3-turbo"

# Allowed audio MIME types for transcription
ALLOWED_AUDIO_TYPES = {
    'audio/webm', 'audio/wav', 'audio/mpeg', 'audio/mp4',
    'audio/ogg', 'audio/mp3', 'audio/m4a', 'audio/x-m4a',
}


def _cosine_similarity(a, b):
    """Compute cosine similarity between two vectors (lists of floats)."""
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(x * x for x in b))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


def _embed_query(client, text):
    """Embed a single query string. Returns a list of floats or None."""
    try:
        response = client.embeddings.create(
            input=text,
            model=EMBEDDING_MODEL,
        )
        return response.data[0].embedding
    except Exception as e:
        print(f"[search] _embed_query failed: {e}")
        traceback.print_exc()
        return None


def _item_text(item):
    """Build the searchable text string for an item."""
    parts = [item.item_name or ""]
    if item.category:
        parts.append(item.category.name)
    if item.item_desc:
        parts.append(item.item_desc)
    return " — ".join(parts)


def embed_item(item):
    """Compute and store an embedding for a single item.
    Called from item create/update routes. Returns True on success."""
    client = get_dedalus_client()
    if client is None:
        return False
    try:
        text = _item_text(item)
        response = client.embeddings.create(
            input=text,
            model=EMBEDDING_MODEL,
        )
        item.embedding = json.dumps(response.data[0].embedding)
        return True
    except Exception as e:
        print(f"[search] embed_item failed: {e}")
        traceback.print_exc()
        return False


# ─── Semantic Search ────────────────────────────────────────────────

@bp.route('/api/search', methods=['POST'])
def semantic_search():
    """
    Accepts JSON: { "query": "...", "categories": [...], "radius": 5,
                    "lat": 40.44, "lng": -79.99 }
    Returns ranked items with a similarity score.
    Falls back to empty results if Dedalus is unavailable.
    """
    data = request.get_json(silent=True) or {}
    query = (data.get('query') or '').strip()

    if not query:
        return jsonify({'results': [], 'fallback': True}), 200

    client = get_dedalus_client()
    if client is None:
        # SDK not available — tell the frontend to use client-side search
        return jsonify({'results': [], 'fallback': True}), 200

    # Embed the query
    query_vec = _embed_query(client, query)
    if query_vec is None:
        return jsonify({'results': [], 'fallback': True}), 200

    # Load all available items with their embeddings
    items = Item.query.options(
        joinedload(Item.location),
        joinedload(Item.category),
        joinedload(Item.owner),
    ).filter_by(is_available=True).all()

    # Optional filters from request
    categories = data.get('categories')  # list or None

    scored = []
    print(f"[search] Query: '{query}', items: {len(items)}, categories: {categories}")
    for item in items:
        # Category filter (hard filter — user explicitly chose categories)
        if categories and 'all' not in categories:
            cat_name = item.category.name if item.category else ''
            if cat_name not in categories:
                continue

        # Similarity — skip items without embeddings
        if not item.embedding:
            continue
        try:
            item_vec = json.loads(item.embedding)
        except (json.JSONDecodeError, TypeError):
            continue

        sim = _cosine_similarity(query_vec, item_vec)
        scored.append((sim, item))

    print(f"[search] Scored {len(scored)} items after filtering (from {len(items)} total)")
    if scored:
        top = scored[0] if scored else None
        scored_sorted = sorted(scored, key=lambda x: x[0], reverse=True)
        print(f"[search] Top match: '{scored_sorted[0][1].item_name}' score={scored_sorted[0][0]:.4f}")

    # Sort by similarity descending
    scored.sort(key=lambda x: x[0], reverse=True)

    # Return top 50
    results = []
    for sim, item in scored[:50]:
        d = item.to_dict()
        d['score'] = round(sim, 4)
        results.append(d)

    return jsonify({'results': results, 'fallback': False}), 200


def _haversine_miles(lat1, lng1, lat2, lng2):
    """Haversine distance in miles."""
    R = 3958.8
    d_lat = math.radians(lat2 - lat1)
    d_lng = math.radians(lng2 - lng1)
    a = (math.sin(d_lat / 2) ** 2 +
         math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) *
         math.sin(d_lng / 2) ** 2)
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


# ─── Voice Transcription ────────────────────────────────────────────

@bp.route('/api/transcribe', methods=['POST'])
def transcribe_audio():
    """
    Accepts a multipart audio file upload.
    Returns JSON: { "text": "transcribed words" }
    """
    client = get_dedalus_client()
    if client is None:
        return jsonify({'error': 'Voice search unavailable (API key not configured)'}), 503

    if 'audio' not in request.files:
        return jsonify({'error': 'No audio file provided'}), 400

    audio_file = request.files['audio']

    try:
        audio_bytes = audio_file.read()
        if len(audio_bytes) == 0:
            return jsonify({'error': 'Empty audio file'}), 400

        print(f"[transcribe] Audio size: {len(audio_bytes)} bytes, content_type: {audio_file.content_type}")

        # Pass as a named tuple so the SDK sends the correct filename/MIME type
        # The upstream API needs the file extension to detect the format
        file_tuple = ("recording.webm", audio_bytes, audio_file.content_type or "audio/webm")

        transcription = client.audio.transcriptions.create(
            file=file_tuple,
            model=TRANSCRIPTION_MODEL,
            language="en",
            response_format="json",
        )

        print(f"[transcribe] SDK response type: {type(transcription)}")
        print(f"[transcribe] SDK response: {transcription}")

        # Handle different possible response shapes
        if hasattr(transcription, 'text'):
            text = transcription.text
        elif isinstance(transcription, dict):
            text = transcription.get('text', '')
        elif isinstance(transcription, str):
            text = transcription
        else:
            text = str(transcription)

        return jsonify({'text': text or ''}), 200

    except Exception as e:
        print(f"[transcribe] ERROR: {e}")
        traceback.print_exc()
        return jsonify({'error': f'Transcription failed: {str(e)}'}), 500

"""
Batch-embed all existing items using Dedalus Labs embeddings API.

Usage:
    cd /path/to/ember
    python -m app.util.embed_items

This will compute and store an embedding vector for every Item that
doesn't already have one. Safe to re-run — it skips items that
already have embeddings unless --force is passed.
"""

import json
import sys
import os

# Ensure project root is on sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from dotenv import load_dotenv
load_dotenv()

from app import app
from app.extensions import db, get_dedalus_client
from app.models import Item

EMBEDDING_MODEL = "openai/text-embedding-3-small"
BATCH_SIZE = 64  # Dedalus supports up to 2048 inputs per request


def item_text(item):
    """Build the text string that gets embedded for an item."""
    parts = [item.item_name or ""]
    if item.category:
        parts.append(item.category.name)
    if item.item_desc:
        parts.append(item.item_desc)
    return " — ".join(parts)


def embed_texts(client, texts):
    """Call Dedalus embeddings API for a batch of texts. Returns list of vectors."""
    response = client.embeddings.create(
        input=texts,
        model=EMBEDDING_MODEL,
    )
    # Sort by index to preserve order
    sorted_data = sorted(response.data, key=lambda d: d.index)
    return [d.embedding for d in sorted_data]


def main(force=False):
    client = get_dedalus_client()
    if client is None:
        print("ERROR: DEDALUS_API_KEY not configured. Set it in .env and try again.")
        sys.exit(1)

    with app.app_context():
        if force:
            items = Item.query.all()
        else:
            items = Item.query.filter(
                (Item.embedding == None) | (Item.embedding == '')
            ).all()

        if not items:
            print("All items already have embeddings. Use --force to re-embed.")
            return

        print(f"Embedding {len(items)} items...")

        for i in range(0, len(items), BATCH_SIZE):
            batch = items[i:i + BATCH_SIZE]
            texts = [item_text(it) for it in batch]
            vectors = embed_texts(client, texts)

            for item, vec in zip(batch, vectors):
                item.embedding = json.dumps(vec)

            db.session.commit()
            print(f"  Batch {i // BATCH_SIZE + 1}: embedded {len(batch)} items")

        print("Done!")


if __name__ == "__main__":
    force = "--force" in sys.argv
    main(force=force)

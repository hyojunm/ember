from flask import jsonify
from .models import Item


@app.route('/api/items')
def get_items():
    items = Item.query.filter_by(is_available=True).all()

    return jsonify([{
        'id': i.id,
        'item_name': i.item_name,
        'item_desc': i.item_desc,
        'latitude': i.latitude,
        'longitude': i.longitude,
        'user_id': i.user_id
    } for i in items])
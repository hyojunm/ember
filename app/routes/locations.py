from flask import Blueprint, request, jsonify
from ..extensions import db
from ..models import Location

bp = Blueprint('locations', __name__)


@bp.route('/api/locations', methods=['GET'])
def get_locations():
    locations = Location.query.all()
    return jsonify([{
        'id': loc.id,
        'name': loc.name,
        'address': loc.address,
        'latitude': loc.latitude,
        'longitude': loc.longitude
    } for loc in locations])


@bp.route('/api/locations', methods=['POST'])
def create_location():
    data = request.get_json()

    location = Location(
        name=data.get('name'),
        address=data['address'],
        latitude=data['latitude'],
        longitude=data['longitude']
    )

    db.session.add(location)
    db.session.commit()

    return jsonify({
        'id': location.id,
        'name': location.name,
        'address': location.address,
        'latitude': location.latitude,
        'longitude': location.longitude
    }), 201

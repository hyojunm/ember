from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from ..extensions import db
from ..models import Location, SavedLocation

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
@login_required
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


@bp.route('/api/saved-locations', methods=['GET'])
@login_required
def get_saved_locations():
    """Get all saved locations for the current user"""
    locations = current_user.get_saved_locations()
    return jsonify(locations), 200


@bp.route('/api/saved-locations', methods=['POST'])
@login_required
def create_saved_location():
    """Create a new saved location"""
    data = request.get_json()
    name = data.get('name')
    address = data.get('address')
    latitude = data.get('latitude')
    longitude = data.get('longitude')
    
    if not all([name, address, latitude, longitude]):
        return jsonify({'error': 'Missing required fields'}), 400
    
    location = current_user.add_saved_location(name, address, latitude, longitude)
    db.session.commit()
    
    return jsonify(location.to_dict()), 201


@bp.route('/api/saved-locations/<int:location_id>', methods=['DELETE'])
@login_required
def delete_saved_location(location_id):
    """Delete a saved location"""
    success = current_user.remove_saved_location(location_id)
    if success:
        db.session.commit()
        return jsonify({'message': 'Location deleted'}), 200
    return jsonify({'error': 'Location not found'}), 404

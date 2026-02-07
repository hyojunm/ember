from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from ..extensions import db
from ..models import Item, Category, Location
import os

bp = Blueprint('items', __name__)

# Note: GET /api/items route remains in app/__init__.py for now.

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@bp.route('/api/items/<int:item_id>', methods=['GET'])
def get_item(item_id):
    """Get a single item by ID"""
    item = Item.query.get_or_404(item_id)
    return jsonify(item.to_dict()), 200


@bp.route('/api/items', methods=['POST'])
@login_required
def create_item():
    """Create a new item listing"""
    try:
        # Get form data
        item_name = request.form.get('item_name')
        is_borrow = request.form.get('is_borrow', 'false').lower() == 'true'
        item_desc = request.form.get('item_desc')
        quantity = request.form.get('quantity', 1, type=int)
        category_name = request.form.get('category')
        pickup_instructions = request.form.get('pickup_instructions')
        
        # Location data
        location_name = request.form.get('location_name')
        address = request.form.get('address')
        latitude = request.form.get('latitude', type=float)
        longitude = request.form.get('longitude', type=float)
        
        # Validation
        if not item_name or not address or latitude is None or longitude is None:
            return jsonify({'error': 'Missing required fields'}), 400
        
        # Get or create category
        category = Category.query.filter_by(name=category_name).first()
        if not category:
            category = Category(name=category_name)
            db.session.add(category)
            db.session.flush()
        
        # Get or create location
        location = Location.query.filter_by(
            latitude=latitude,
            longitude=longitude
        ).first()
        
        if not location:
            location = Location(
                name=location_name,
                address=address,
                latitude=latitude,
                longitude=longitude
            )
            db.session.add(location)
            db.session.flush()
        
        # Handle file upload
        picture_filename = None
        if 'picture' in request.files:
            file = request.files['picture']
            if file and file.filename and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                # Add user_id to filename to avoid conflicts
                picture_filename = f"{current_user.id}_{filename}"
                
                from flask import current_app
                upload_folder = current_app.config.get('UPLOAD_FOLDER')
                if upload_folder:
                    os.makedirs(upload_folder, exist_ok=True)
                    file.save(os.path.join(upload_folder, picture_filename))
        
        # Create new item
        new_item = Item(
            user_id=current_user.id,
            item_name=item_name,
            is_borrow=is_borrow,
            item_desc=item_desc,
            quantity=quantity,
            category_id=category.id,
            location_id=location.id,
            pickup_instructions=pickup_instructions,
            picture=picture_filename,
            is_available=True
        )
        
        db.session.add(new_item)
        db.session.commit()
        
        return jsonify({
            'message': 'Item created successfully',
            'item': new_item.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@bp.route('/api/items/<int:item_id>', methods=['PUT', 'PATCH'])
@login_required
def update_item(item_id):
    """Update an existing item listing"""
    try:
        item = Item.query.get_or_404(item_id)
        
        # Check ownership
        if item.user_id != current_user.id:
            return jsonify({'error': 'Unauthorized'}), 403
        
        # Update fields if provided
        if 'item_name' in request.form:
            item.item_name = request.form.get('item_name')
        
        if 'is_borrow' in request.form:
            item.is_borrow = request.form.get('is_borrow', 'false').lower() == 'true'
        
        if 'item_desc' in request.form:
            item.item_desc = request.form.get('item_desc')
        
        if 'quantity' in request.form:
            item.quantity = request.form.get('quantity', type=int)
        
        if 'is_available' in request.form:
            item.is_available = request.form.get('is_available', 'true').lower() == 'true'
        
        if 'pickup_instructions' in request.form:
            item.pickup_instructions = request.form.get('pickup_instructions')
        
        # Update category if provided
        if 'category' in request.form:
            category_name = request.form.get('category')
            category = Category.query.filter_by(name=category_name).first()
            if not category:
                category = Category(name=category_name)
                db.session.add(category)
                db.session.flush()
            item.category_id = category.id
        
        # Update location if provided
        if 'latitude' in request.form and 'longitude' in request.form:
            latitude = request.form.get('latitude', type=float)
            longitude = request.form.get('longitude', type=float)
            address = request.form.get('address')
            location_name = request.form.get('location_name')
            
            if latitude is not None and longitude is not None and address:
                location = Location.query.filter_by(
                    latitude=latitude,
                    longitude=longitude
                ).first()
                
                if not location:
                    location = Location(
                        name=location_name,
                        address=address,
                        latitude=latitude,
                        longitude=longitude
                    )
                    db.session.add(location)
                    db.session.flush()
                
                item.location_id = location.id
        
        # Handle file upload
        if 'picture' in request.files:
            file = request.files['picture']
            if file and file.filename and allowed_file(file.filename):
                # Delete old picture if exists
                if item.picture:
                    from flask import current_app
                    upload_folder = current_app.config.get('UPLOAD_FOLDER')
                    if upload_folder:
                        old_path = os.path.join(upload_folder, item.picture)
                        if os.path.exists(old_path):
                            os.remove(old_path)
                
                # Save new picture
                filename = secure_filename(file.filename)
                picture_filename = f"{current_user.id}_{filename}"
                
                from flask import current_app
                upload_folder = current_app.config.get('UPLOAD_FOLDER')
                if upload_folder:
                    os.makedirs(upload_folder, exist_ok=True)
                    file.save(os.path.join(upload_folder, picture_filename))
                    item.picture = picture_filename
        
        db.session.commit()
        
        return jsonify({
            'message': 'Item updated successfully',
            'item': item.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@bp.route('/api/items/<int:item_id>', methods=['DELETE'])
@login_required
def delete_item(item_id):
    """Delete an item listing"""
    try:
        item = Item.query.get_or_404(item_id)
        
        # Check ownership
        if item.user_id != current_user.id:
            return jsonify({'error': 'Unauthorized'}), 403
        
        # Delete associated picture file if exists
        if item.picture:
            from flask import current_app
            upload_folder = current_app.config.get('UPLOAD_FOLDER')
            if upload_folder:
                picture_path = os.path.join(upload_folder, item.picture)
                if os.path.exists(picture_path):
                    os.remove(picture_path)
        
        db.session.delete(item)
        db.session.commit()
        
        return jsonify({'message': 'Item deleted successfully'}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

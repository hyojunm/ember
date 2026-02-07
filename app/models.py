from datetime import datetime
from .extensions import db
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)

    # account information
    username = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)

    # contact information
    phone_number = db.Column(db.String(20)) # Critical for offline SMS contact
    phone_public = db.Column(db.Boolean, default=False)
    
    # Relationship: One user can share many items
    items = db.relationship('Item', backref='owner', lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class Item(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    # Core Details
    item_name = db.Column(db.String(100), nullable=False)
    is_borrow = db.Column(db.Boolean, default=False)
    item_desc = db.Column(db.Text)
    quantity = db.Column(db.Integer, default=1)
    
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'), nullable=False)
    category = db.relationship('Category', backref='items', lazy=True)
    
    # Status Tracking
    is_available = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Geography
    location_id = db.Column(db.Integer, db.ForeignKey('location.id'), nullable=False)
    pickup_instructions = db.Column(db.Text) # e.g. "On the porch"
    
    # picture
    picture = db.Column(db.String(100)) # Path to image file

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.item_name,
            'category': self.category.name if self.category else "Uncategorized",
            'is_borrow': self.is_borrow,
            'description': self.item_desc,
            'quantity': self.quantity,
            'available': self.is_available,
            'created_at': self.created_at.isoformat(),
            'latitude': self.location.latitude,
            'longitude': self.location.longitude,
            'address': self.location.address,
            'location_name': self.location.name,
            'owner_name': self.owner.username,
            'picture': self.picture
        }


class Category(db.Model): # Optional: If you want a strict list
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True)


class Location(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    
    name = db.Column(db.String(100))
    address = db.Column(db.String(100), nullable=False)

    latitude = db.Column(db.Float, nullable=False)
    longitude = db.Column(db.Float, nullable=False)

    items = db.relationship('Item', backref='location', lazy=True)
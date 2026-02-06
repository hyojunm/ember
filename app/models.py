from datetime import datetime
from flask_login import UserMixin
from .extensions import db
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
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'), nullable=False)
    is_borrow = db.Column(db.Boolean, default=False)
    item_desc = db.Column(db.Text)
    quantity = db.Column(db.Integer, default=1)
    
    # Status Tracking
    is_available = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Geography
    location_id = db.Column(db.Integer, db.ForeignKey('location.id'))
    latitude = db.Column(db.Float) # Best for Leaflet/Offline Maps
    longitude = db.Column(db.Float)
    pickup_instructions = db.Column(db.Text) # e.g. "On the porch"
    
    # picture
    picture = db.Column(db.String(100)) # Path to image file


class Category(db.Model): # Optional: If you want a strict list
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True)


class Location(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    latitude = db.Column(db.Float, nullable=False)
    longitude = db.Column(db.Float, nullable=False)
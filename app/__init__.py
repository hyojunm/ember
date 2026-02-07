from .extensions import db, login_manager
from flask import Flask
from flask import jsonify, render_template, send_from_directory, redirect, url_for
from flask_login import current_user
from .models import Item, User
import os
import mimetypes

app = Flask(__name__)
base_dir = os.path.abspath(os.path.dirname(__file__))

# --- DATABASE & SECURITY CONFIG ---

# Use environment variable for Secret Key in production, fallback to 'BoilerUp!' for local dev
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'BoilerUp!')

# Get the Neon DATABASE_URL from Vercel environment variables
database_url = os.environ.get('DATABASE_URL')

# FIX: SQLAlchemy 1.4+ requires "postgresql://" but Neon/Vercel provides "postgres://"
if database_url and database_url.startswith("postgres://"):
    database_url = database_url.replace("postgres://", "postgresql://", 1)

# If DATABASE_URL exists, use it (Neon). Otherwise, use local SQLite.
app.config['SQLALCHEMY_DATABASE_URI'] = database_url or 'sqlite:///' + os.path.join(base_dir, 'site.db')

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = os.path.join(base_dir, 'static', 'uploads')
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# --- INITIALIZE EXTENSIONS ---
db.init_app(app)
login_manager.init_app(app)

# Add pmtiles support
mimetypes.add_type('application/vnd.pmtiles', '.pmtiles')


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# --- REGISTER BLUEPRINTS ---
from .routes import users, health, items, locations

app.register_blueprint(users.bp)
app.register_blueprint(health.bp)
app.register_blueprint(items.bp)
app.register_blueprint(locations.bp)


# --- ROUTES ---

@app.route('/')
def main():
    return render_template('homepage.html')


@app.route('/create-listing')
def create_listing():
    if not current_user.is_authenticated:
        return redirect(url_for("users.login"))
    return render_template('create_new_listing.html')


@app.route('/edit-listing/<int:item_id>')
def edit_listing(item_id):
    return render_template('edit_item.html', item_id=item_id)


@app.route('/account-info')
def account_info():
    return render_template('account_info.html')


@app.route('/api/items', methods=['GET'])
def get_items():
    # Load items and 'eagerly' join their related location and category
    items = Item.query.options(
        joinedload(Item.location),
        joinedload(Item.category),
        joinedload(Item.owner)
    ).filter_by(is_available=True).all()

    return jsonify([item.to_dict() for item in items])


# --- STATIC FILE SERVING ---

@app.route('/sw.js')
def serve_sw():
    response = send_from_directory(os.path.join(app.root_path, 'static/js'), 'sw.js')
    response.headers['Service-Worker-Allowed'] = '/'

    return response


@app.route('/manifest.json')
def serve_manifest():
    return send_from_directory(os.path.join(app.root_path, 'static'), 'manifest.json')


@app.route('/uploads/<filename>')
def serve_upload(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)


@app.route('/static/maps/<path:filename>')
def serve_pmtiles(filename):
    path = os.path.join(app.root_path, 'static/maps', filename)
    size = os.path.getsize(path)
    
    response = send_from_directory(os.path.join(app.root_path, 'static/maps'), filename, conditional=True)
    
    # Force these headers to satisfy Mac/Unix byte-serving
    response.headers['Cache-Control'] = 'public, max-age=31536000'
    response.headers['Content-Length'] = size
    response.headers['Accept-Ranges'] = 'bytes'
    response.headers['Content-Type'] = 'application/octet-stream'
    
    return response
    # 'conditional=True' tells Flask to support HTTP Range Requests
    # response = send_from_directory(os.path.join(app.root_path, 'static/maps'), filename, conditional=True)
    # response.headers['Cache-Control'] = 'public, max-age=31536000'
    # response.headers['Accept-Ranges'] = 'bytes'
    # response.headers['Content-Type'] = 'application/octet-stream'

    # return response


if __name__ == '__main__':
    app.run()
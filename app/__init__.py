from .extensions import db, login_manager
from flask import Flask
from flask import jsonify, render_template, send_from_directory
from .models import Item, User
from sqlalchemy.orm import joinedload
import os


app = Flask(__name__)
base_dir = os.path.abspath(os.path.dirname(__file__))

app.config['SECRET_KEY'] = 'BoilerUp!' # TODO: use environment variable
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(base_dir, 'site.db') # TODO: use postgresql
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False # ???

db.init_app(app)
login_manager.init_app(app)


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# Register blueprints
from .routes import users, health, items
app.register_blueprint(users.bp)
app.register_blueprint(health.bp)
app.register_blueprint(items.bp)


@app.route('/')
def main():
    return render_template('main.html')


@app.route('/api/items', methods=['GET'])
def get_items():
    # Load items and 'eagerly' join their related location and category
    items = Item.query.options(
        joinedload(Item.location),
        joinedload(Item.category),
        joinedload(Item.owner)
    ).filter_by(is_available=True).all()
    
    return jsonify([item.to_dict() for item in items])


# serve pwa files from root
@app.route('/sw.js')
def serve_sw():
    return send_from_directory(os.path.join(app.root_path, 'static/js'), 'sw.js')


@app.route('/manifest.json')
def serve_manifest():
    return send_from_directory(os.path.join(app.root_path, 'static'), 'manifest.json')


if __name__ == '__main__':
    app.run()
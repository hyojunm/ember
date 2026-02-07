from .extensions import db, login_manager
from flask import Flask
from flask import jsonify, flash, redirect, render_template, request, send_from_directory, url_for
from flask_login import current_user, login_user, logout_user
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


@app.route('/')
def main():
    return render_template('main.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main'))

    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        remember = True if request.form.get('remember') else False
        
        if User.query.filter_by(username=username).first():
            flash('Username already exists.', 'danger')
        else:
            new_user = User(username=username)
            new_user.set_password(password)

            db.session.add(new_user)
            db.session.commit()
            
            login_user(new_user, remember=remember)
            return redirect(url_for('main'))

    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main'))

    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        remember = True if request.form.get('remember') else False

        user = User.query.filter_by(username=username).first()

        if user and user.check_password(password):
            login_user(user, remember=remember)
            flash(f'Welcome back, {username}!', 'success')
            
            # if the user was redirected here from a protected page, 
            # take them back there, otherwise go to main.
            next_page = request.args.get('next')

            return redirect(next_page) if next_page else redirect(url_for('main'))
        else:
            flash('Incorrect username or password.', 'danger')

    return render_template('login.html')


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('login'))


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
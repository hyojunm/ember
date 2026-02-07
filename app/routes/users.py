from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import current_user, login_user, logout_user
from ..extensions import db
from ..models import User

bp = Blueprint('users', __name__)


@bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('health.main'))

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
            return redirect(url_for('health.main'))

    return render_template('register.html')


@bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('health.main'))

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

            return redirect(next_page) if next_page else redirect(url_for('health.main'))
        else:
            flash('Incorrect username or password.', 'danger')

    return render_template('login.html')


@bp.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('users.login'))

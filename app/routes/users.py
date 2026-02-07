from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import current_user, login_user, logout_user, login_required
from ..extensions import db
from ..models import User

bp = Blueprint('users', __name__)


@bp.route('/create-account', methods=['GET', 'POST'])
def create_account():
    if current_user.is_authenticated:
        return redirect(url_for('main'))

    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        phone = request.form.get('phone')

        if not username or not password:
            flash('Username and password are required.', 'danger')
        elif password != confirm_password:
            flash('Passwords do not match.', 'danger')
        elif User.query.filter_by(username=username).first():
            flash('Username already exists.', 'danger')
        else:
            new_user = User(username=username, phone_number=phone)
            new_user.set_password(password)

            db.session.add(new_user)
            db.session.commit()

            login_user(new_user)
            flash(f'Welcome to Ember, {username}!', 'success')
            return redirect(url_for('main'))

    return render_template('create_account.html')


@bp.route('/login', methods=['GET', 'POST'])
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

            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('main'))
        else:
            flash('Incorrect username or password.', 'danger')

    return render_template('login.html')


@bp.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('users.login'))


@bp.route('/account-info')
@login_required
def account_info():
    return render_template('account_info.html')


@bp.route('/api/update-profile', methods=['POST'])
@login_required
def update_profile():
    """Update user profile information"""
    try:
        data = request.get_json()
        field = data.get('field')
        value = data.get('value')
        
        if field == 'username':
            # Check if username is taken
            if value != current_user.username:
                existing = User.query.filter_by(username=value).first()
                if existing:
                    return jsonify({'error': 'Username already taken'}), 400
            current_user.username = value
            
        elif field == 'phone_number':
            current_user.phone_number = value
            
        elif field == 'phone_public':
            current_user.phone_public = value.lower() == 'true'
        
        else:
            return jsonify({'error': 'Invalid field'}), 400
        
        db.session.commit()
        return jsonify({'message': 'Profile updated successfully'}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@bp.route('/api/change-password', methods=['POST'])
@login_required
def change_password():
    """Change user password"""
    try:
        data = request.get_json()
        current_password = data.get('current_password')
        new_password = data.get('new_password')
        
        if not current_password or not new_password:
            return jsonify({'error': 'Current password and new password are required'}), 400
        
        # Verify current password
        if not current_user.check_password(current_password):
            return jsonify({'error': 'Current password is incorrect'}), 400
        
        # Update password
        current_user.set_password(new_password)
        db.session.commit()
        
        return jsonify({'message': 'Password changed successfully'}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@bp.route('/api/delete-account', methods=['DELETE'])
@login_required
def delete_account():
    """Delete user account"""
    try:
        user_id = current_user.id
        
        # Delete user (cascade will handle related items and saved locations)
        user = User.query.get(user_id)
        db.session.delete(user)
        db.session.commit()
        
        # Log out the user
        logout_user()
        
        return jsonify({'message': 'Account deleted successfully'}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500
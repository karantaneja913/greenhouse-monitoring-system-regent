from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from werkzeug.security import check_password_hash
from models import db, User # Import db and User from models

auth_bp = Blueprint('auth', __name__, template_folder='../templates') # Point to the main templates folder

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        user = User.query.filter_by(email=email).first()
        
        if user and check_password_hash(user.password, password):
            session.permanent = True # Make session permanent based on config
            session['user_id'] = user.id
            session['user_name'] = user.name
            session['user_role'] = user.role
            flash('Login successful!', 'success')
            # Redirect to the main dashboard, which will be in a different blueprint
            return redirect(url_for('main.dashboard')) 
        else:
            flash('Invalid email or password', 'error')
            return redirect(url_for('auth.login')) # Redirect back to login page on failure
    
    # If GET request or failed POST, render login page
    # Check if user is already logged in, redirect to dashboard if so
    if 'user_id' in session:
        return redirect(url_for('main.dashboard'))
    return render_template('login.html')

@auth_bp.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('auth.login')) # Redirect to login page after logout

from flask import Blueprint, render_template, redirect, url_for, session, flash, current_app
from datetime import datetime
import json
from models import db, User, Greenhouse, Reading, Employee, Issue # Import necessary models

main_bp = Blueprint('main', __name__, template_folder='../templates')

@main_bp.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('main.dashboard'))
    # Render login page at root if not logged in (handled by auth blueprint now)
    return redirect(url_for('auth.login')) # Redirect to login page

@main_bp.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        flash('Please log in to access the dashboard.', 'warning')
        return redirect(url_for('auth.login'))
    
    # Get greenhouse stats for dashboard
    total_greenhouses = Greenhouse.query.count()
    critical_issues_count = Greenhouse.query.filter_by(status='critical').count()
    warning_issues_count = Greenhouse.query.filter_by(status='warning').count()
    
    # Get resolved issues today
    today = datetime.utcnow().date()
    resolved_today = Issue.query.filter(
        db.func.date(Issue.resolved_at) == today,
        Issue.status == 'resolved'
    ).count()
    
    # Get all greenhouses with their latest readings
    greenhouses = Greenhouse.query.all()
    greenhouse_data = []
    
    for gh in greenhouses:
        latest_reading = Reading.query.filter_by(greenhouse_id=gh.id).order_by(Reading.timestamp.desc()).first()
        
        # Determine reading status for display
        temp_status = 'normal'
        humidity_status = 'normal'
        air_quality_status = 'normal'
        soil_moisture_status = 'normal'
        
        if latest_reading:
            # Use thresholds (consider moving to config or constants)
            CRITICAL_TEMP_HIGH = 35
            CRITICAL_TEMP_LOW = 10
            WARNING_TEMP_HIGH = 30
            WARNING_TEMP_LOW = 15
            CRITICAL_HUMIDITY_HIGH = 90
            CRITICAL_HUMIDITY_LOW = 30
            WARNING_HUMIDITY_HIGH = 85
            WARNING_HUMIDITY_LOW = 40

            if latest_reading.temperature > CRITICAL_TEMP_HIGH or latest_reading.temperature < CRITICAL_TEMP_LOW: temp_status = 'critical'
            elif latest_reading.temperature > WARNING_TEMP_HIGH or latest_reading.temperature < WARNING_TEMP_LOW: temp_status = 'warning'
            
            if latest_reading.humidity > CRITICAL_HUMIDITY_HIGH or latest_reading.humidity < CRITICAL_HUMIDITY_LOW: humidity_status = 'critical'
            elif latest_reading.humidity > WARNING_HUMIDITY_HIGH or latest_reading.humidity < WARNING_HUMIDITY_LOW: humidity_status = 'warning'
            
            if latest_reading.air_quality == 'Poor': air_quality_status = 'critical'
            elif latest_reading.air_quality == 'Fair': air_quality_status = 'warning'
            
            if latest_reading.soil_moisture == 'Very Low': soil_moisture_status = 'critical'
            elif latest_reading.soil_moisture == 'Low': soil_moisture_status = 'warning'
            
        greenhouse_data.append({
            'id': gh.id,
            'name': gh.name,
            'status': gh.status,
            'temperature': latest_reading.temperature if latest_reading else 'N/A',
            'humidity': latest_reading.humidity if latest_reading else 'N/A',
            'air_quality': latest_reading.air_quality if latest_reading else 'N/A',
            'soil_moisture': latest_reading.soil_moisture if latest_reading else 'N/A',
            'temp_status': temp_status,
            'humidity_status': humidity_status,
            'air_quality_status': air_quality_status,
            'soil_moisture_status': soil_moisture_status
        })
    
    # Get available employees for modal
    available_employees = Employee.query.filter_by(status='available').all()
    
    return render_template('dashboard.html', 
                          total_greenhouses=total_greenhouses,
                          critical_issues=critical_issues_count,
                          warning_issues=warning_issues_count,
                          resolved_today=resolved_today,
                          greenhouses=greenhouse_data,
                          available_employees=available_employees)

@main_bp.route('/settings')
def settings():
    if 'user_id' not in session:
        flash('Please log in to access this page.', 'warning')
        return redirect(url_for('auth.login'))
    
    # If admin, show all users
    users = []
    if session.get('user_role') == 'admin':
        users = User.query.all()
    
    return render_template('settings.html', users=users)

@main_bp.route('/profile')
def profile():
    if 'user_id' not in session:
        flash('Please log in to access this page.', 'warning')
        return redirect(url_for('auth.login'))
    
    user = User.query.get(session['user_id'])
    if not user:
        session.clear() # Clear session if user not found
        flash('User not found. Please log in again.', 'error')
        return redirect(url_for('auth.login'))
        
    return render_template('profile.html', user=user)

from flask import Blueprint, render_template, redirect, url_for, session, flash, current_app
import json
from models import db, Greenhouse, Reading, Issue, Employee # Import necessary models

greenhouses_bp = Blueprint('greenhouses', __name__, template_folder='../templates')

@greenhouses_bp.route('/greenhouses')
def list_greenhouses(): # Renamed function to avoid conflict
    if 'user_id' not in session:
        flash('Please log in to access this page.', 'warning')
        return redirect(url_for('auth.login'))
    
    greenhouses = Greenhouse.query.all()
    greenhouse_data = []
    
    for gh in greenhouses:
        latest_reading = Reading.query.filter_by(greenhouse_id=gh.id).order_by(Reading.timestamp.desc()).first()
        open_issues = Issue.query.filter_by(greenhouse_id=gh.id, status='open').count()
        assigned_issues = Issue.query.filter_by(greenhouse_id=gh.id, status='assigned').count()
        
        temp_status = 'normal'
        humidity_status = 'normal'
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
            
        greenhouse_data.append({
            'id': gh.id,
            'name': gh.name,
            'location': gh.location,
            'status': gh.status,
            'temperature': latest_reading.temperature if latest_reading else 'N/A',
            'humidity': latest_reading.humidity if latest_reading else 'N/A',
            'air_quality': latest_reading.air_quality if latest_reading else 'N/A',
            'soil_moisture': latest_reading.soil_moisture if latest_reading else 'N/A',
            'open_issues': open_issues,
            'assigned_issues': assigned_issues,
            'temp_status': temp_status,
            'humidity_status': humidity_status
        })
    
    return render_template('greenhouses.html', greenhouses=greenhouse_data)

@greenhouses_bp.route('/greenhouse/<int:id>')
def greenhouse_detail(id):
    if 'user_id' not in session:
        flash('Please log in to access this page.', 'warning')
        return redirect(url_for('auth.login'))
    
    greenhouse = Greenhouse.query.get_or_404(id)
    latest_reading = Reading.query.filter_by(greenhouse_id=id).order_by(Reading.timestamp.desc()).first()
    
    # Determine reading statuses
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

    # Get historical readings for charts (last 30 readings)
    historical_readings = Reading.query.filter_by(greenhouse_id=id).order_by(Reading.timestamp.desc()).limit(30).all()
    historical_readings.reverse()  # Oldest first for charts
    
    reading_dates = [reading.timestamp.strftime('%H:%M %d-%b') for reading in historical_readings] # Format for readability
    temperatures = [reading.temperature for reading in historical_readings]
    humidities = [reading.humidity for reading in historical_readings]
    
    # Get open issues
    open_issues = Issue.query.filter_by(greenhouse_id=id).filter(Issue.status != 'resolved').all()
    
    # Get available employees for assignment
    available_employees = Employee.query.filter_by(status='available').all()
    
    return render_template('greenhouse_detail.html', 
                          greenhouse=greenhouse,
                          latest_reading=latest_reading,
                          temp_status=temp_status,
                          humidity_status=humidity_status,
                          air_quality_status=air_quality_status,
                          soil_moisture_status=soil_moisture_status,
                          reading_dates=json.dumps(reading_dates),
                          temperatures=json.dumps(temperatures),
                          humidities=json.dumps(humidities),
                          open_issues=open_issues,
                          available_employees=available_employees)

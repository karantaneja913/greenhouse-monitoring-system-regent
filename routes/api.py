from flask import Blueprint, jsonify, request, session, current_app
from models import db, Employee, Greenhouse, Reading, Issue, Notification, User # Import necessary models
from datetime import datetime, timedelta

api_bp = Blueprint('api', __name__, url_prefix='/api') # Add url_prefix for all routes in this blueprint

# --- API Endpoints ---

@api_bp.route('/employees', methods=['GET'])
def api_get_employees():
    # Basic protection - could be enhanced based on roles
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 401
        
    employees = Employee.query.all()
    result = []
    for employee in employees:
        result.append({
            'id': employee.id,
            'name': employee.name,
            'email': employee.email,
            'phone': employee.phone,
            'status': employee.status,
            # Add issue counts if needed by tests/frontend API consumers
            'assigned_issues': Issue.query.filter_by(employee_id=employee.id, status='assigned').count()
        })
    return jsonify(result)

@api_bp.route('/greenhouses', methods=['GET'])
def api_get_greenhouses():
     # Basic protection - could be enhanced based on roles
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 401

    greenhouses = Greenhouse.query.all()
    result = []
    for gh in greenhouses:
        latest_reading = Reading.query.filter_by(greenhouse_id=gh.id).order_by(Reading.timestamp.desc()).first()
        result.append({
            'id': gh.id,
            'name': gh.name,
            'location': gh.location,
            'status': gh.status,
            'latest_reading': {
                'temperature': latest_reading.temperature if latest_reading else None,
                'humidity': latest_reading.humidity if latest_reading else None,
                'air_quality': latest_reading.air_quality if latest_reading else None,
                'soil_moisture': latest_reading.soil_moisture if latest_reading else None,
                'light_level': latest_reading.light_level if latest_reading else None,
                'timestamp': latest_reading.timestamp.isoformat() if latest_reading else None
            } if latest_reading else None,
             'open_issues': Issue.query.filter_by(greenhouse_id=gh.id, status='open').count(),
             'assigned_issues': Issue.query.filter_by(greenhouse_id=gh.id, status='assigned').count()
        })
    return jsonify(result)


@api_bp.route('/assign-employee', methods=['POST'])
def assign_employee():
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 401
    
    data = request.json
    greenhouse_id = data.get('greenhouse_id')
    employee_id = data.get('employee_id')
    priority = data.get('priority')
    notes = data.get('notes')
    
    # Validate input
    if not all([greenhouse_id, employee_id, priority]):
        return jsonify({'success': False, 'message': 'Missing required fields'}), 400
        
    # Check if employee and greenhouse exist
    employee = Employee.query.get(employee_id)
    greenhouse = Greenhouse.query.get(greenhouse_id)
    
    if not employee or not greenhouse:
        return jsonify({'success': False, 'message': 'Employee or greenhouse not found'}), 404
    
    # Find or create issue
    # Find open or assigned issues for this greenhouse to avoid duplicates
    issue = Issue.query.filter_by(greenhouse_id=greenhouse_id).filter(Issue.status.in_(['open', 'assigned'])).first()
    
    if not issue:
        # Create a new issue if none exists or the existing one is resolved
        issue = Issue(
            greenhouse_id=greenhouse_id,
            employee_id=employee_id,
            issue_type='environmental', # Or determine based on greenhouse status/readings
            description=f'Issue reported in {greenhouse.name}',
            priority=priority,
            status='assigned',
            notes=notes
        )
        db.session.add(issue)
    else:
        # Update existing open/assigned issue
        issue.employee_id = employee_id
        issue.priority = priority
        issue.status = 'assigned'
        issue.notes = notes # Overwrite or append notes as needed
    
    # Update employee status
    employee.status = 'busy'
    
    # Create notification for the assigning user
    notification = Notification(
        user_id=session['user_id'],
        title=f'Assignment - {greenhouse.name}',
        message=f'{employee.name} has been assigned to resolve issues at {greenhouse.name}',
        notification_type='info',
        related_greenhouse=greenhouse_id
    )
    db.session.add(notification)
    
    # Optionally, notify the assigned employee if they are also a user
    assigned_user = User.query.filter_by(email=employee.email).first()
    if assigned_user:
         employee_notification = Notification(
            user_id=assigned_user.id,
            title=f'New Assignment - {greenhouse.name}',
            message=f'You have been assigned to resolve issues at {greenhouse.name}. Priority: {priority}',
            notification_type='info',
            related_greenhouse=greenhouse_id
        )
         db.session.add(employee_notification)

    db.session.commit()
    
    return jsonify({
        'success': True, 
        'message': f'Employee {employee.name} assigned to {greenhouse.name}'
    })

@api_bp.route('/resolve-issue', methods=['POST'])
def resolve_issue():
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 401
    
    data = request.json
    greenhouse_id = data.get('greenhouse_id')
    
    # Check if greenhouse exists
    greenhouse = Greenhouse.query.get(greenhouse_id)
    if not greenhouse:
        return jsonify({'success': False, 'message': 'Greenhouse not found'}), 404
    
    # Find open or assigned issues for this greenhouse
    issues = Issue.query.filter_by(greenhouse_id=greenhouse_id).filter(Issue.status.in_(['open', 'assigned'])).all()
    
    if not issues:
        # If no open/assigned issues, maybe the button shouldn't have been enabled?
        # Or maybe just update greenhouse status if it's not normal
        if greenhouse.status != 'normal':
             greenhouse.status = 'normal'
             db.session.commit()
             return jsonify({'success': True, 'message': f'No active issues found. {greenhouse.name} status set to normal.'})
        else:
             return jsonify({'success': False, 'message': 'No active issues found for this greenhouse'}), 404

    resolved_count = 0
    for issue in issues:
        resolved_count += 1
        issue.status = 'resolved'
        issue.resolved_at = datetime.utcnow()
        
        # Update employee status if no other active issues
        if issue.employee_id:
            employee = Employee.query.get(issue.employee_id)
            if employee: # Check if employee exists
                other_active_issues = Issue.query.filter(
                    Issue.employee_id == employee.id, 
                    Issue.status == 'assigned',
                    Issue.id != issue.id # Exclude the current issue being resolved
                ).count()
                
                if other_active_issues == 0:
                    employee.status = 'available'
    
    # Update greenhouse status only if issues were resolved
    if resolved_count > 0:
        greenhouse.status = 'normal'
    
        # Create notification
        notification = Notification(
            user_id=session['user_id'],
            title=f'Issue Resolved - {greenhouse.name}',
            message=f'{resolved_count} issue(s) at {greenhouse.name} have been marked as resolved',
            notification_type='success',
            related_greenhouse=greenhouse_id
        )
        db.session.add(notification)
    
    db.session.commit()
    
    return jsonify({
        'success': True, 
        'message': f'{resolved_count} issue(s) resolved for {greenhouse.name}'
    })

@api_bp.route('/readings/add', methods=['POST'])
def add_reading():
    # This endpoint might be used by sensors or manually
    data = request.json
    greenhouse_id = data.get('greenhouse_id')
    
    # Validate greenhouse exists
    greenhouse = Greenhouse.query.get(greenhouse_id)
    if not greenhouse:
        return jsonify({'success': False, 'message': 'Greenhouse not found'}), 404
    
    # Basic validation for readings
    try:
        temp = float(data.get('temperature'))
        humidity = float(data.get('humidity'))
        light_level = float(data.get('light_level'))
        air_quality = str(data.get('air_quality'))
        soil_moisture = str(data.get('soil_moisture'))
    except (ValueError, TypeError):
         return jsonify({'success': False, 'message': 'Invalid reading data format'}), 400

    reading = Reading(
        greenhouse_id=greenhouse_id,
        temperature=temp,
        humidity=humidity,
        air_quality=air_quality,
        soil_moisture=soil_moisture,
        light_level=light_level
    )
    
    db.session.add(reading)
    
    # Check if values are within acceptable ranges and update greenhouse status
    old_status = greenhouse.status
    new_status = 'normal'
    issue_priority = None
    issue_description = None
    notification_type = 'info'
    notification_title = None
    notification_message = None

    # Define thresholds (could be moved to config or DB)
    CRITICAL_TEMP_HIGH = 35
    CRITICAL_TEMP_LOW = 10
    WARNING_TEMP_HIGH = 30
    WARNING_TEMP_LOW = 15
    CRITICAL_HUMIDITY_HIGH = 90
    CRITICAL_HUMIDITY_LOW = 30
    WARNING_HUMIDITY_HIGH = 85
    WARNING_HUMIDITY_LOW = 40

    # Determine status based on readings
    if (temp > CRITICAL_TEMP_HIGH or temp < CRITICAL_TEMP_LOW or 
        humidity > CRITICAL_HUMIDITY_HIGH or humidity < CRITICAL_HUMIDITY_LOW or 
        air_quality == 'Poor'):
        new_status = 'critical'
        issue_priority = 'critical' # Priority should be critical for critical status
        issue_description = f"Critical readings: Temp={temp}°C, Humidity={humidity}%, Air Quality={air_quality}"
        notification_type = 'critical'
        notification_title = f'Critical Alert - {greenhouse.name}'
        notification_message = issue_description
        
    elif (temp > WARNING_TEMP_HIGH or temp < WARNING_TEMP_LOW or 
          humidity > WARNING_HUMIDITY_HIGH or humidity < WARNING_HUMIDITY_LOW or 
          soil_moisture == 'Low' or soil_moisture == 'Very Low' or # Include Very Low as warning too
          air_quality == 'Fair'): # Add Fair air quality as warning
        new_status = 'warning'
        issue_priority = 'high' # Keep high priority for warnings
        issue_description = f"Warning readings: Temp={temp}°C, Humidity={humidity}%, Soil={soil_moisture}, Air={air_quality}"
        notification_type = 'warning'
        notification_title = f'Warning - {greenhouse.name}'
        notification_message = issue_description

    # Update greenhouse status if changed
    if new_status != old_status:
        greenhouse.status = new_status
        
        # Create issue only if moving into warning/critical state
        if new_status in ['warning', 'critical']:
            existing_issue = Issue.query.filter_by(greenhouse_id=greenhouse_id).filter(Issue.status != 'resolved').first()
            if not existing_issue:
                # Determine priority again right before creating, just to be safe
                current_issue_priority = 'critical' if new_status == 'critical' else 'high'
                issue = Issue(
                    greenhouse_id=greenhouse_id,
                    issue_type='environmental',
                    priority=current_issue_priority, # Use explicitly determined priority
                    description=issue_description,
                    status='open' # New issues start as open
                )
                db.session.add(issue)
        
        # Create notification for status change (for logged-in users)
        if 'user_id' in session and notification_title:
             # Notify all admin/manager users? Or just the current user if they added manually?
             # For now, notify the user who triggered the action (if manual) or potentially admins
             admin_users = User.query.filter(User.role.in_(['admin', 'manager'])).all()
             user_ids_to_notify = {user.id for user in admin_users}
             if session['user_id'] not in user_ids_to_notify: # Add current user if not admin/manager
                 user_ids_to_notify.add(session['user_id'])

             for user_id in user_ids_to_notify:
                 notification = Notification(
                    user_id=user_id,
                    title=notification_title,
                    message=notification_message,
                    notification_type=notification_type,
                    related_greenhouse=greenhouse_id
                 )
                 db.session.add(notification)

    db.session.commit()
    
    return jsonify({'success': True, 'message': 'Reading added successfully', 'new_status': new_status})

@api_bp.route('/notifications', methods=['GET'])
def get_notifications():
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 401
    
    notifications = Notification.query.filter_by(user_id=session['user_id']).order_by(Notification.created_at.desc()).limit(10).all()
    
    result = []
    for notification in notifications:
        result.append({
            'id': notification.id,
            'title': notification.title,
            'message': notification.message,
            'is_read': notification.is_read,
            'notification_type': notification.notification_type,
            'created_at': notification.created_at.isoformat(), # Use ISO format for JS parsing
            'related_greenhouse': notification.related_greenhouse
        })
    
    return jsonify(result)

@api_bp.route('/notifications/mark-read', methods=['POST'])
def mark_notifications_read():
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 401
    
    data = request.json
    notification_id = data.get('notification_id')
    
    if notification_id:
        # Mark a single notification as read
        notification = Notification.query.filter_by(id=notification_id, user_id=session['user_id']).first()
        if notification:
            notification.is_read = True
            db.session.commit()
            return jsonify({'success': True, 'message': 'Notification marked as read'})
        else:
             return jsonify({'success': False, 'message': 'Notification not found'}), 404
    else:
        # Mark all notifications as read
        updated_count = Notification.query.filter_by(user_id=session['user_id'], is_read=False).update({'is_read': True})
        db.session.commit()
        return jsonify({'success': True, 'message': f'{updated_count} notifications marked as read'})

@api_bp.route('/statistics', methods=['GET'])
def get_statistics():
    # No auth check needed if this is for public display or internal use?
    # If auth needed:
    # if 'user_id' not in session:
    #     return jsonify({'success': False, 'message': 'Unauthorized'}), 401
    
    # Total greenhouses
    total_greenhouses = Greenhouse.query.count()
    
    # Critical and warning issues (based on greenhouse status)
    critical_issues_count = Greenhouse.query.filter_by(status='critical').count()
    warning_issues_count = Greenhouse.query.filter_by(status='warning').count()
    
    # Resolved issues today
    today = datetime.utcnow().date()
    resolved_today = Issue.query.filter(
        db.func.date(Issue.resolved_at) == today,
        Issue.status == 'resolved'
    ).count()
    
    # Issues by type (active issues)
    issue_types = db.session.query(Issue.issue_type, db.func.count(Issue.id)).\
        filter(Issue.status != 'resolved').\
        group_by(Issue.issue_type).all()
    issues_by_type = {issue_type: count for issue_type, count in issue_types}
    
    # Get 30-day trend data (using date objects for filtering)
    trend_data = []
    today_date = datetime.utcnow().date()
    for i in range(30):
        day = today_date - timedelta(days=29-i)
        
        critical_count = Issue.query.filter(
            db.func.date(Issue.created_at) == day, 
            Issue.priority.in_(['critical']) # Match critical priority
        ).count()
        
        warning_count = Issue.query.filter(
            db.func.date(Issue.created_at) == day, 
            Issue.priority.in_(['high', 'medium']) # Match warning priorities
        ).count()
        
        resolved_count = Issue.query.filter(
            db.func.date(Issue.resolved_at) == day,
            Issue.status == 'resolved'
        ).count()
        
        trend_data.append({
            'day': day.strftime('%d-%b'), # Format day for labels
            'critical': critical_count,
            'warning': warning_count,
            'resolved': resolved_count
        })
    
    return jsonify({
        'total_greenhouses': total_greenhouses,
        'critical_issues': critical_issues_count,
        'warning_issues': warning_issues_count,
        'resolved_today': resolved_today,
        'issues_by_type': issues_by_type,
        'trend_data': trend_data
    })

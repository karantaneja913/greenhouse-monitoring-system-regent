from flask import Blueprint, flash, redirect, url_for, current_app
from werkzeug.security import generate_password_hash
from models import db, User, Greenhouse, Employee, Reading, Issue, Notification # Import necessary models
from datetime import datetime, timedelta
import random
import os

init_db_bp = Blueprint('init_db', __name__)

# Initialize the database with sample data
@init_db_bp.route('/init-db')
def init_db_command(): # Renamed function
    # Check if DB already has data to prevent accidental overwrite
    # Use app context to access db
    with current_app.app_context():
        if Greenhouse.query.first() or User.query.first():
             flash("Database already initialized.", 'warning')
             return redirect(url_for('auth.login')) # Redirect to login or dashboard

        # Drop and recreate tables
        db.drop_all() # Use with caution in production
        db.create_all()
        
        # Create admin user
        admin = User(
            name='Karan Taneja',
            email='karan.taneja@greentech.com',
            password=generate_password_hash('password123', method='pbkdf2:sha256'), # Default password
            role='admin'
        )
        db.session.add(admin)

        # Create other sample users
        users = [
            User(name='Saran Singh', email='saran.singh@greentech.com', password=generate_password_hash('password123', method='pbkdf2:sha256'), role='manager'),
            User(name='Nikul Makwana', email='nikul.makwana@greentech.com', password=generate_password_hash('password123', method='pbkdf2:sha256'), role='manager'),
            User(name='Fazar', email='fazar@greentech.com', password=generate_password_hash('password123', method='pbkdf2:sha256'), role='user'),
            User(name='Karanpreet Singh', email='karanpreet.singh@greentech.com', password=generate_password_hash('password123', method='pbkdf2:sha256'), role='user'),
            User(name='Gourav', email='gourav@greentech.com', password=generate_password_hash('password123', method='pbkdf2:sha256'), role='user')
        ]
        db.session.add_all(users)

        # Create sample greenhouses
        greenhouses = []
        for i in range(1, 13):
            gh = Greenhouse(
                name=f'Greenhouse #{i}',
                location=f'Sector {chr(64 + (i % 4 + 1))}-{ (i // 4) + 1 }', # Example location
                status='normal'
            )
            greenhouses.append(gh)
        db.session.add_all(greenhouses)

        # Create sample employees using the same names as users
        employees = [
            Employee(name='Karan Taneja', email='karan.taneja@greentech.com', phone='123-456-7890', status='available'),
            Employee(name='Saran Singh', email='saran.singh@greentech.com', phone='123-456-7891', status='available'),
            Employee(name='Nikul Makwana', email='nikul.makwana@greentech.com', phone='123-456-7892', status='available'),
            Employee(name='Fazar', email='fazar@greentech.com', phone='123-456-7893', status='available'),
            Employee(name='Karanpreet Singh', email='karanpreet.singh@greentech.com', phone='123-456-7894', status='available'),
            Employee(name='Gourav', email='gourav@greentech.com', phone='123-456-7895', status='busy') # Example busy employee
        ]
        db.session.add_all(employees)

        db.session.commit() # Commit users, greenhouses, employees first to get IDs
        
        # Add initial readings and issues for each greenhouse
        admin_user_id = admin.id # Get admin ID after commit
        
        for gh in Greenhouse.query.all(): # Query again to get committed objects with IDs
            # Set different statuses for a few greenhouses
            if gh.id == 1:
                gh.status = 'critical'
            elif gh.id == 2:
                gh.status = 'warning'
            elif gh.id == 4:
                gh.status = 'warning'
            
            # Create readings with appropriate values based on status
            temp = 24
            humidity = 65
            air_quality = 'Good'
            soil_moisture = 'Good'
            light = 700
            
            if gh.status == 'critical':
                temp = 38
                humidity = 65
                air_quality = 'Fair'
                soil_moisture = 'Good'
                light = 850
                
                # Create a critical issue
                issue = Issue(
                    greenhouse_id=gh.id,
                    issue_type='environmental',
                    description='Temperature critically high',
                    priority='critical',
                    status='open'
                )
                db.session.add(issue)
                
                # Create notification for admin
                notification = Notification(user_id=admin_user_id, title=f'Critical Alert - {gh.name}', message=issue.description, notification_type='critical', related_greenhouse=gh.id)
                db.session.add(notification)

            elif gh.status == 'warning':
                temp = 25
                humidity = 78
                air_quality = 'Good'
                soil_moisture = 'Low'
                light = 750
                
                # Create a warning issue
                issue = Issue(
                    greenhouse_id=gh.id,
                    issue_type='environmental',
                    description='High humidity and low soil moisture',
                    priority='high', # Changed from medium
                    status='open'
                )
                db.session.add(issue)
                
                # Create notification for admin
                notification = Notification(user_id=admin_user_id, title=f'Warning - {gh.name}', message=issue.description, notification_type='warning', related_greenhouse=gh.id)
                db.session.add(notification)
                
            # Add the latest reading
            reading = Reading(
                greenhouse_id=gh.id,
                temperature=temp,
                humidity=humidity,
                air_quality=air_quality,
                soil_moisture=soil_moisture,
                light_level=light
            )
            db.session.add(reading)
            
            # Add some historical readings for charts
            for j in range(1, 31):
                historical_reading = Reading(
                    greenhouse_id=gh.id,
                    temperature=round(random.uniform(20, 30), 1),
                    humidity=round(random.uniform(50, 80), 1),
                    air_quality=random.choice(['Good', 'Good', 'Good', 'Fair']),
                    soil_moisture=random.choice(['Good', 'Good', 'Low']),
                    light_level=round(random.uniform(600, 900)),
                    timestamp=datetime.utcnow() - timedelta(days=j, hours=random.randint(0, 23))
                )
                db.session.add(historical_reading)
        
        # Create some initial notifications for the admin
        notifications = [
            Notification(
                user_id=admin_user_id,
                title='System Initialized',
                message='The GreenTech Monitoring System database has been initialized.',
                notification_type='info',
                created_at=datetime.utcnow() - timedelta(minutes=30)
            ),
             Notification(
                user_id=admin_user_id,
                title='Issue Resolved - Greenhouse #5', # Example resolved notification
                message='All parameters have returned to normal',
                notification_type='success',
                related_greenhouse=5, # Assuming GH #5 exists
                is_read=True, # Mark as read
                created_at=datetime.utcnow() - timedelta(minutes=20)
            )
        ]
        db.session.add_all(notifications)
        
        db.session.commit()
        
        flash('Database initialized with sample data!', 'success')
        return redirect(url_for('auth.login')) # Redirect to login after init

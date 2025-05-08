import os
from flask import Flask
from config import config_by_name
from models import db, User, Greenhouse, Employee, Reading, Issue, Notification # Import db and all models
from routes.utils import register_context_processors # Import context processor registration function
from werkzeug.security import generate_password_hash
from datetime import datetime, timedelta
import random

def _seed_initial_data(current_app_instance):
    """Seeds the database with initial sample data if it's empty."""
    with current_app_instance.app_context():
        # Check if DB already has data to prevent accidental overwrite
        if Greenhouse.query.first() or User.query.first():
            print("Database already contains data. Skipping seed.")
            return

        print("Seeding initial data...")

        # Create admin user
        admin = User(
            name='Karan Taneja',
            email='karan.taneja@greentech.com',
            password=generate_password_hash('password123', method='pbkdf2:sha256'), # Default password
            role='admin'
        )
        db.session.add(admin)

        # Create other sample users
        users_data = [
            {'name': 'Saran Singh', 'email': 'saran.singh@greentech.com', 'role': 'manager'},
            {'name': 'Nikul Makwana', 'email': 'nikul.makwana@greentech.com', 'role': 'manager'},
            {'name': 'Fazar', 'email': 'fazar@greentech.com', 'role': 'user'},
            {'name': 'Karanpreet Singh', 'email': 'karanpreet.singh@greentech.com', 'role': 'user'},
            {'name': 'Gourav', 'email': 'gourav@greentech.com', 'role': 'user'}
        ]
        for u_data in users_data:
            user = User(name=u_data['name'], email=u_data['email'], password=generate_password_hash('password123', method='pbkdf2:sha256'), role=u_data['role'])
            db.session.add(user)

        # Create sample greenhouses
        greenhouses_list = []
        for i in range(1, 13):
            gh = Greenhouse(
                name=f'Greenhouse #{i}',
                location=f'Sector {chr(64 + (i % 4 + 1))}-{ (i // 4) + 1 }', # Example location
                status='normal'
            )
            greenhouses_list.append(gh)
        db.session.add_all(greenhouses_list)

        # Create sample employees
        employees_data = [
            {'name': 'Karan Taneja', 'email': 'karan.taneja@greentech.com', 'phone': '123-456-7890', 'status': 'available'},
            {'name': 'Saran Singh', 'email': 'saran.singh@greentech.com', 'phone': '123-456-7891', 'status': 'available'},
            {'name': 'Nikul Makwana', 'email': 'nikul.makwana@greentech.com', 'phone': '123-456-7892', 'status': 'available'},
            {'name': 'Fazar', 'email': 'fazar@greentech.com', 'phone': '123-456-7893', 'status': 'available'},
            {'name': 'Karanpreet Singh', 'email': 'karanpreet.singh@greentech.com', 'phone': '123-456-7894', 'status': 'available'},
            {'name': 'Gourav', 'email': 'gourav@greentech.com', 'phone': '123-456-7895', 'status': 'busy'}
        ]
        for emp_data in employees_data:
            employee = Employee(name=emp_data['name'], email=emp_data['email'], phone=emp_data['phone'], status=emp_data['status'])
            db.session.add(employee)
        
        db.session.commit() # Commit users, greenhouses, employees first to get IDs
        
        admin_user_id = User.query.filter_by(email='karan.taneja@greentech.com').first().id

        for gh_committed in Greenhouse.query.all():
            temp_val, humidity_val, air_q_val, soil_m_val, light_val = 24, 65, 'Good', 'Good', 700
            
            if gh_committed.id == 1:
                gh_committed.status = 'critical'
                temp_val, humidity_val, air_q_val, soil_m_val, light_val = 38, 65, 'Fair', 'Good', 850
                issue = Issue(greenhouse_id=gh_committed.id, issue_type='environmental', description='Temperature critically high', priority='critical', status='open')
                db.session.add(issue)
                db.session.add(Notification(user_id=admin_user_id, title=f'Critical Alert - {gh_committed.name}', message=issue.description, notification_type='critical', related_greenhouse=gh_committed.id))
            elif gh_committed.id == 2 or gh_committed.id == 4:
                gh_committed.status = 'warning'
                temp_val, humidity_val, air_q_val, soil_m_val, light_val = 25, 78, 'Good', 'Low', 750
                issue_desc = 'High humidity and low soil moisture' if gh_committed.id == 2 else 'Soil moisture low'
                issue = Issue(greenhouse_id=gh_committed.id, issue_type='environmental', description=issue_desc, priority='high', status='open')
                db.session.add(issue)
                db.session.add(Notification(user_id=admin_user_id, title=f'Warning - {gh_committed.name}', message=issue.description, notification_type='warning', related_greenhouse=gh_committed.id))
            
            db.session.add(Reading(greenhouse_id=gh_committed.id, temperature=temp_val, humidity=humidity_val, air_quality=air_q_val, soil_moisture=soil_m_val, light_level=light_val))
            
            for j in range(1, 31):
                db.session.add(Reading(
                    greenhouse_id=gh_committed.id,
                    temperature=round(random.uniform(20, 30), 1),
                    humidity=round(random.uniform(50, 80), 1),
                    air_quality=random.choice(['Good', 'Good', 'Good', 'Fair']),
                    soil_moisture=random.choice(['Good', 'Good', 'Low']),
                    light_level=round(random.uniform(600, 900)),
                    timestamp=datetime.utcnow() - timedelta(days=j, hours=random.randint(0, 23))
                ))
        
        initial_notifications = [
            Notification(user_id=admin_user_id, title='System Initialized', message='The GreenTech Monitoring System database has been initialized.', notification_type='info', created_at=datetime.utcnow() - timedelta(minutes=30)),
            Notification(user_id=admin_user_id, title='Issue Resolved - Greenhouse #5', message='All parameters have returned to normal', notification_type='success', related_greenhouse=5, is_read=True, created_at=datetime.utcnow() - timedelta(minutes=20))
        ]
        db.session.add_all(initial_notifications)
        
        db.session.commit()
        print("Initial data seeding completed.")


def create_app(config_name='default'):
    """Application Factory Function"""
    app = Flask(__name__)
    
    # Load configuration
    app.config.from_object(config_by_name[config_name])
    
    # Initialize extensions
    db.init_app(app)
    
    # Register context processors
    register_context_processors(app)

    # Register Blueprints
    from routes.auth import auth_bp
    app.register_blueprint(auth_bp)

    from routes.main import main_bp
    app.register_blueprint(main_bp)

    from routes.greenhouses import greenhouses_bp
    app.register_blueprint(greenhouses_bp)

    from routes.employees import employees_bp
    app.register_blueprint(employees_bp)

    from routes.reports import reports_bp
    app.register_blueprint(reports_bp)

    from routes.api import api_bp
    app.register_blueprint(api_bp)

    from routes.init_db import init_db_bp # Keep this for manual re-init if ever needed
    app.register_blueprint(init_db_bp)

    # Ensure the instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass # Already exists

    with app.app_context():
        db.create_all() # Create database tables if they don't exist
        _seed_initial_data(app) # Seed data if DB is empty

    return app

# Create the app instance for development run
app = create_app(os.getenv('FLASK_CONFIG') or 'default')

# Main application entry point for running with `python app.py`
if __name__ == '__main__':
    # Use the configuration setting for debug mode
    app.run(debug=app.config.get('DEBUG', True), use_reloader=False) # Added use_reloader=False for seeding

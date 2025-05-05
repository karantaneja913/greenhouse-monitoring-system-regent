from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

# Database Models
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(20), default='user')  # admin, manager, user
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Greenhouse(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    location = db.Column(db.String(200))
    status = db.Column(db.String(20), default='normal')  # normal, warning, critical
    readings = db.relationship('Reading', backref='greenhouse', lazy=True)
    issues = db.relationship('Issue', backref='greenhouse', lazy=True)

class Reading(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    greenhouse_id = db.Column(db.Integer, db.ForeignKey('greenhouse.id'), nullable=False)
    temperature = db.Column(db.Float)
    humidity = db.Column(db.Float)
    air_quality = db.Column(db.String(20))
    soil_moisture = db.Column(db.String(20))
    light_level = db.Column(db.Float)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

class Employee(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20))
    status = db.Column(db.String(20), default='available')  # available, busy
    issues = db.relationship('Issue', backref='assigned_employee', lazy=True)

class Issue(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    greenhouse_id = db.Column(db.Integer, db.ForeignKey('greenhouse.id'), nullable=False)
    employee_id = db.Column(db.Integer, db.ForeignKey('employee.id'), nullable=True)
    issue_type = db.Column(db.String(50), nullable=False)
    description = db.Column(db.Text)
    priority = db.Column(db.String(20), default='medium')  # low, medium, high, critical
    status = db.Column(db.String(20), default='open')  # open, assigned, resolved
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    resolved_at = db.Column(db.DateTime)
    notes = db.Column(db.Text)

class Notification(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True) # Should link to User model
    title = db.Column(db.String(100), nullable=False)
    message = db.Column(db.Text, nullable=False)
    is_read = db.Column(db.Boolean, default=False)
    notification_type = db.Column(db.String(20), default='info')  # info, warning, critical, success
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    related_greenhouse = db.Column(db.Integer, db.ForeignKey('greenhouse.id'), nullable=True)

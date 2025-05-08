import unittest
import json
# To import app and db, we need to adjust the Python path or use relative imports carefully.
# Assuming 'app.py' is in the parent directory of 'tests'.
import sys
import os

# Add the project root to the Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

from app import app, db # Now app and db should be importable
from models import User, Greenhouse, Employee, Issue, Reading # Import all necessary models
from werkzeug.security import generate_password_hash
from datetime import datetime, timedelta

class BaseTestCase(unittest.TestCase):
    """Base class for tests, sets up a test Flask app and in-memory DB."""

    def setUp(self):
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        app.config['WTF_CSRF_ENABLED'] = False  # Disable CSRF for testing forms if any
        app.config['SECRET_KEY'] = 'test_secret_key' # Consistent secret key for session
        
        self.app_context = app.app_context()
        self.app_context.push() # Push an application context
        
        db.create_all()
        self.client = app.test_client() # Use self.client consistently

        # Common test data can be created here if needed by many test classes
        # Or create specific test data in derived classes' setUp methods

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop() # Pop the application context

    def _create_test_user(self, email='test@example.com', password='password', role='user', name='Test User'):
        user = User(
            name=name,
            email=email,
            password=generate_password_hash(password, method='pbkdf2:sha256'),
            role=role
        )
        db.session.add(user)
        db.session.commit()
        return user

    def _login_user(self, email='test@example.com', password='password'):
        """Helper to log in a user via POST request to login route."""
        # Ensure the user exists or create one
        user = User.query.filter_by(email=email).first()
        if not user:
            self._create_test_user(email=email, password=password)
        
        response = self.client.post('/login', data=dict(
            email=email,
            password=password
        ), follow_redirects=True)
        return response

    def _login_user_session(self, user_id, user_role='user'):
        """Simulate login by setting session variable for the test client."""
        with self.client.session_transaction() as sess:
            sess['user_id'] = user_id
            sess['user_role'] = user_role
            sess['_fresh'] = True # Common for Flask-Login

    def _create_test_greenhouse(self, name='Test GH', location='Sector A', status='normal'):
        gh = Greenhouse(name=name, location=location, status=status)
        db.session.add(gh)
        db.session.commit()
        return gh

    def _create_test_employee(self, name='Test Emp', email='employee@example.com', status='available'):
        emp = Employee(name=name, email=email, status=status)
        db.session.add(emp)
        db.session.commit()
        return emp

if __name__ == '__main__':
    unittest.main()

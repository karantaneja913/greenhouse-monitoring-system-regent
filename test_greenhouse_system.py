# test_greenhouse_system.py
import unittest
import json
from app import app, db, Greenhouse, Reading, Employee, Issue, User # Import User
from werkzeug.security import generate_password_hash # Import hasher
from datetime import datetime, timedelta

class TestGreenhouseSystem(unittest.TestCase):
    def setUp(self):
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        self.app = app.test_client()
        with app.app_context():
            db.create_all()

            # Setup test data - User, Greenhouse, Employee
            test_user = User(name='Test User', email='test@test.com', password=generate_password_hash('password'), role='admin')
            greenhouse = Greenhouse(name='Test Greenhouse', location='Test Location', status='normal')
            employee = Employee(name='Test Employee', email='test@example.com', status='available') # Use different email from user

            db.session.add(test_user)
            db.session.add(greenhouse)
            db.session.add(employee)
            db.session.commit()

            # Store IDs after commit
            self.user_id = test_user.id
            self.greenhouse_id = greenhouse.id
            self.employee_id = employee.id

            # Simulate login by setting session variable for the test client
            with self.app.session_transaction() as sess:
                sess['user_id'] = self.user_id
                sess['user_role'] = 'admin' # Set role if needed by endpoints

    def tearDown(self):
        with app.app_context():
            db.session.remove()
            db.drop_all()

    # API Tests (Now assuming authentication is handled in setUp)
    def test_get_greenhouses(self):
        response = self.app.get('/api/greenhouses')
        self.assertEqual(response.status_code, 200) # Should now pass auth
        data = json.loads(response.data)
        # Expecting 1 greenhouse created in setUp
        self.assertGreaterEqual(len(data), 1) # Check if at least one exists
        self.assertEqual(data[0]['name'], 'Test Greenhouse') # Check the specific one

    def test_get_employees(self):
        response = self.app.get('/api/employees')
        self.assertEqual(response.status_code, 200) # Should now pass auth
        data = json.loads(response.data)
         # Expecting 1 employee created in setUp
        self.assertGreaterEqual(len(data), 1) # Check if at least one exists
        self.assertEqual(data[0]['name'], 'Test Employee') # Check the specific one

    # Integration Tests (Now assuming authentication is handled in setUp)
    def test_assign_and_resolve_issue(self):
        # First assign an employee to an issue
        assign_data = {
            'greenhouse_id': self.greenhouse_id,
            'employee_id': self.employee_id,
            'priority': 'high', # Keep as high, the API should handle creating/updating
            'notes': 'Test issue'
        }

        # Use the correct API endpoint
        response = self.app.post('/api/assign-employee',
                                 data=json.dumps(assign_data),
                                 content_type='application/json')

        self.assertEqual(response.status_code, 200) # Should now pass auth
        assign_result = json.loads(response.data)
        self.assertTrue(assign_result['success'])

        # Check if issue was created and employee status updated
        with app.app_context():
            issue = Issue.query.filter_by(greenhouse_id=self.greenhouse_id).first() # Query more specifically
            self.assertIsNotNone(issue, "Issue was not created/updated")
            self.assertEqual(issue.greenhouse_id, self.greenhouse_id)
            self.assertEqual(issue.employee_id, self.employee_id)
            self.assertEqual(issue.status, 'assigned') # Status should be assigned

            employee = db.session.get(Employee, self.employee_id) # Use Session.get for PK lookup
            self.assertIsNotNone(employee, "Employee not found for status check")
            self.assertEqual(employee.status, 'busy')

        # Now resolve the issue
        resolve_data = {
            'greenhouse_id': self.greenhouse_id
        }

        # Use the correct API endpoint
        response = self.app.post('/api/resolve-issue',
                                 data=json.dumps(resolve_data),
                                 content_type='application/json')

        self.assertEqual(response.status_code, 200) # Should now pass auth
        resolve_result = json.loads(response.data)
        self.assertTrue(resolve_result['success'])

        # Check if issue status and employee status were updated
        with app.app_context():
            issue = Issue.query.filter_by(greenhouse_id=self.greenhouse_id).first() # Query more specifically
            self.assertIsNotNone(issue, "Issue not found for resolved check")
            self.assertEqual(issue.status, 'resolved')
            self.assertIsNotNone(issue.resolved_at)

            employee = db.session.get(Employee, self.employee_id) # Use Session.get
            self.assertIsNotNone(employee, "Employee not found for available check")
            self.assertEqual(employee.status, 'available')

            greenhouse = db.session.get(Greenhouse, self.greenhouse_id) # Use Session.get
            self.assertIsNotNone(greenhouse, "Greenhouse not found for status check")
            self.assertEqual(greenhouse.status, 'normal')


    def test_add_reading_creates_issue(self):
        # Add a critical reading
        reading_data = {
            'greenhouse_id': self.greenhouse_id,
            'temperature': 40,  # Critical temperature
            'humidity': 50,
            'air_quality': 'Good',
            'soil_moisture': 'Good',
            'light_level': 1000
        }

        response = self.app.post('/api/readings/add',
                                 data=json.dumps(reading_data),
                                 content_type='application/json')

        # Note: /api/readings/add doesn't seem to have auth check in app.py,
        # but keeping the 200 check consistent.
        self.assertEqual(response.status_code, 200)

        # Check if greenhouse status was updated and issue created
        with app.app_context():
            # Corrected: Use self.greenhouse_id
            greenhouse = db.session.get(Greenhouse, self.greenhouse_id)
            self.assertIsNotNone(greenhouse, "Greenhouse not found after adding reading")
            self.assertEqual(greenhouse.status, 'critical')

            # Corrected: Use self.greenhouse_id
            reading = Reading.query.filter_by(greenhouse_id=self.greenhouse_id).order_by(Reading.timestamp.desc()).first()
            self.assertIsNotNone(reading, "Reading not found")
            self.assertEqual(reading.temperature, 40)

            # Corrected: Use self.greenhouse_id
            issue = Issue.query.filter_by(greenhouse_id=self.greenhouse_id).first()
            self.assertIsNotNone(issue, "Issue not created after critical reading")
            self.assertEqual(issue.greenhouse_id, self.greenhouse_id)
            self.assertEqual(issue.priority, 'critical') # Expect 'critical' priority now
            self.assertEqual(issue.status, 'open')

if __name__ == '__main__':
    unittest.main()

import unittest
from ..base_test import BaseTestCase # Import BaseTestCase from one level up
from models import db, User, Greenhouse, Employee, Reading, Issue, Notification
from datetime import datetime, timedelta
from werkzeug.security import check_password_hash, generate_password_hash

class TestUserModel(BaseTestCase):

    def test_user_creation(self):
        user = self._create_test_user(email='newuser@example.com', name='New User', password='newpassword123', role='manager')
        self.assertIsNotNone(user.id)
        self.assertEqual(user.email, 'newuser@example.com')
        self.assertEqual(user.name, 'New User')
        self.assertEqual(user.role, 'manager')
        self.assertTrue(check_password_hash(user.password, 'newpassword123'))

    def test_user_password_hashing(self):
        hashed_pw = generate_password_hash('securepassword', method='pbkdf2:sha256')
        user = User(name="Hash Test", email="hash@test.com", password=hashed_pw, role="user")
        db.session.add(user)
        db.session.commit()
        
        retrieved_user = User.query.filter_by(email="hash@test.com").first()
        self.assertTrue(check_password_hash(retrieved_user.password, 'securepassword'))
        self.assertFalse(check_password_hash(retrieved_user.password, 'wrongpassword'))

class TestGreenhouseModel(BaseTestCase):

    def test_greenhouse_creation(self):
        gh = self._create_test_greenhouse(name='Orchid House', location='Botanical Gardens', status='warning')
        self.assertIsNotNone(gh.id)
        self.assertEqual(gh.name, 'Orchid House')
        self.assertEqual(gh.location, 'Botanical Gardens')
        self.assertEqual(gh.status, 'warning')

class TestReadingModel(BaseTestCase):
    def test_reading_creation(self):
        gh = self._create_test_greenhouse()
        timestamp_before = datetime.utcnow() - timedelta(seconds=1)
        reading = Reading(
            greenhouse_id=gh.id,
            temperature=25.5,
            humidity=60.2,
            air_quality='Good',
            soil_moisture='Optimal',
            light_level=800
        )
        db.session.add(reading)
        db.session.commit()
        
        self.assertIsNotNone(reading.id)
        self.assertEqual(reading.greenhouse_id, gh.id)
        self.assertEqual(reading.temperature, 25.5)
        self.assertGreaterEqual(reading.timestamp, timestamp_before)
        self.assertLessEqual(reading.timestamp, datetime.utcnow())


class TestIssueModel(BaseTestCase):
    def test_issue_creation_and_relationships(self):
        user = self._create_test_user(email="assignee@example.com", role="user")
        gh = self._create_test_greenhouse()
        emp = self._create_test_employee(email="worker@example.com") # Employee who can be assigned

        issue = Issue(
            greenhouse_id=gh.id,
            reported_by_id=user.id, # Optional: if you track who reported
            employee_id=emp.id,     # Optional: if assigned on creation
            issue_type='equipment',
            description='Sprinkler malfunction',
            priority='high',
            status='open'
        )
        db.session.add(issue)
        db.session.commit()

        self.assertIsNotNone(issue.id)
        self.assertEqual(issue.greenhouse_id, gh.id)
        self.assertEqual(issue.reported_by_id, user.id)
        self.assertEqual(issue.employee_id, emp.id)
        self.assertEqual(issue.description, 'Sprinkler malfunction')
        self.assertEqual(issue.status, 'open')
        
        # Test relationships (if defined in models.py and back_populates correctly)
        # self.assertIn(issue, gh.issues) # Assuming Greenhouse.issues relationship
        # self.assertIn(issue, emp.issues) # Assuming Employee.issues relationship

# Add more model tests as needed for Employee, Notification, etc.

if __name__ == '__main__':
    unittest.main()

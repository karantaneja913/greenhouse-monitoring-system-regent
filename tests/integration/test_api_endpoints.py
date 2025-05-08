import unittest
import json
from ..base_test import BaseTestCase # Import BaseTestCase from one level up
from models import db, User, Greenhouse, Employee # Import necessary models

class TestApiEndpoints(BaseTestCase):

    def setUp(self):
        super().setUp() # Call BaseTestCase.setUp()
        # Create a default admin user and log them in for API tests
        self.admin_user = self._create_test_user(email='admin_api@example.com', role='admin', name='API Admin')
        self._login_user_session(user_id=self.admin_user.id, user_role='admin')
        
        # Create some initial data for GET requests
        self.gh1 = self._create_test_greenhouse(name='API Test GH 1')
        self.emp1 = self._create_test_employee(name='API Test Emp 1')


    def test_get_greenhouses_api(self):
        response = self.client.get('/api/greenhouses')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIsInstance(data, list)
        self.assertGreaterEqual(len(data), 1)
        
        # Check if the created greenhouse is in the list
        found_gh = any(gh['name'] == self.gh1.name for gh in data)
        self.assertTrue(found_gh, "Test greenhouse not found in API response.")

    def test_get_employees_api(self):
        response = self.client.get('/api/employees')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIsInstance(data, list)
        self.assertGreaterEqual(len(data), 1)

        # Check if the created employee is in the list
        found_emp = any(emp['name'] == self.emp1.name for emp in data)
        self.assertTrue(found_emp, "Test employee not found in API response.")

    def test_get_greenhouse_detail_api(self):
        # Test getting a specific greenhouse
        response = self.client.get(f'/api/greenhouses/{self.gh1.id}')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data['name'], self.gh1.name)
        self.assertEqual(data['id'], self.gh1.id)

    def test_get_greenhouse_detail_api_not_found(self):
        non_existent_id = 99999
        response = self.client.get(f'/api/greenhouses/{non_existent_id}')
        self.assertEqual(response.status_code, 404) # Assuming API returns 404

    # Add more API endpoint tests here, e.g., for specific employee, readings for a greenhouse etc.
    # Example: Test readings for a greenhouse
    def test_get_readings_for_greenhouse_api(self):
        # Add some readings for self.gh1
        from models import Reading # Local import if not at top
        reading1 = Reading(greenhouse_id=self.gh1.id, temperature=25, humidity=60)
        reading2 = Reading(greenhouse_id=self.gh1.id, temperature=26, humidity=62)
        db.session.add_all([reading1, reading2])
        db.session.commit()

        response = self.client.get(f'/api/greenhouses/{self.gh1.id}/readings')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIsInstance(data, list)
        self.assertEqual(len(data), 2)
        self.assertEqual(data[0]['temperature'], 25) # Assuming default order or specific order
        self.assertEqual(data[1]['temperature'], 26)


if __name__ == '__main__':
    unittest.main()

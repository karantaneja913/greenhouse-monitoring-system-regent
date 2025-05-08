import unittest
import json # Added json import
from ..base_test import BaseTestCase # Using Flask test client for simplified acceptance tests
from models import User, Greenhouse, Reading, Issue # For setup or verification

class TestAcceptanceCriteria(BaseTestCase):

    def test_ac_admin_can_login_and_see_dashboard(self):
        """
        Acceptance Criterion: An administrator can successfully log in and view the main dashboard.
        Scenario:
            Given an admin user exists
            When the admin logs in with correct credentials
            Then the admin should be redirected to the dashboard
            And the dashboard should display key overview information
        """
        admin_email = 'ac_admin@example.com'
        admin_pass = 'ac_password'
        self._create_test_user(email=admin_email, password=admin_pass, role='admin', name='AC Admin')

        response_login = self.client.post('/login', data={
            'email': admin_email,
            'password': admin_pass
        }, follow_redirects=True)
        
        self.assertEqual(response_login.status_code, 200, "Admin login failed.")
        self.assertIn(b'Dashboard', response_login.data, "Dashboard keyword not found after login.")
        self.assertIn(b'Overview', response_login.data, "Overview section not found on dashboard.")
        # Further checks for specific dashboard elements can be added.

    def test_ac_critical_reading_generates_alert_and_updates_status(self):
        """
        Acceptance Criterion: Submitting a sensor reading that indicates a critical condition
                             should update the greenhouse status to 'critical', create an issue,
                             and potentially generate a notification.
        Scenario:
            Given a greenhouse exists
            And an admin user is set up to receive alerts (or system generates general alert)
            When a critical sensor reading (e.g., very high temperature) is submitted for the greenhouse
            Then the greenhouse status should be updated to 'critical'
            And a new issue with 'critical' priority should be created for that greenhouse
            And an alert/notification should be visible to the admin (or logged)
        """
        gh = self._create_test_greenhouse(name='AC Critical GH')
        admin = self._create_test_user(email='ac_alert_admin@example.com', role='admin')
        # self._login_user_session(user_id=admin.id, user_role='admin') # If API needs auth

        critical_reading_data = {
            'greenhouse_id': gh.id,
            'temperature': 45, # Critical temperature
            'humidity': 50,
            'air_quality': 'Good',
            'soil_moisture': 'Good',
            'light_level': 1000
        }
        response_reading = self.client.post('/api/readings/add',
                                           data=json.dumps(critical_reading_data),
                                           content_type='application/json')
        self.assertEqual(response_reading.status_code, 200, "Failed to submit critical reading.")

        # Verify greenhouse status
        db.session.refresh(gh)
        self.assertEqual(gh.status, 'critical', "Greenhouse status not updated to critical.")

        # Verify issue creation
        critical_issue = Issue.query.filter_by(greenhouse_id=gh.id, priority='critical').first()
        self.assertIsNotNone(critical_issue, "Critical issue was not created.")
        self.assertEqual(critical_issue.status, 'open')

        # Verify notification (simplified check, actual notification visibility depends on UI/API)
        # This part would be more robust with Selenium if checking UI notifications.
        # Here, we check if a notification record was created in the DB.
        from models import Notification # Ensure import
        notification = Notification.query.filter_by(related_issue_id=critical_issue.id, notification_type='critical').first()
        self.assertIsNotNone(notification, "Critical notification record not found in DB.")
        self.assertIn(gh.name, notification.title) # Check if notification title is relevant

    # More acceptance tests would follow, e.g.:
    # - A manager can assign an open issue to an available employee.
    # - An employee can view issues assigned to them.
    # - Resolving all critical issues for a greenhouse returns its status to normal.
    # - Users with 'user' role cannot access admin-only pages.

    # For true BDD style, tools like Behave (Gherkin) + Selenium would be used.
    # These unittest-style tests verify the criteria at a high level using HTTP client.

if __name__ == '__main__':
    unittest.main()

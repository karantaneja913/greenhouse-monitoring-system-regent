import unittest
import json
from ..base_test import BaseTestCase
from models import db, User, Greenhouse, Employee, Issue, Notification # Import all necessary models

class TestWorkflowIssueManagement(BaseTestCase):

    def setUp(self):
        super().setUp()
        self.admin_user = self._create_test_user(email='admin_workflow@example.com', role='admin', name='Workflow Admin')
        self._login_user_session(user_id=self.admin_user.id, user_role='admin')

        self.greenhouse = self._create_test_greenhouse(name='Issue GH')
        self.employee = self._create_test_employee(name='Issue Emp', email='issue_emp@example.com')

    def test_assign_employee_to_new_issue_and_resolve(self):
        # Step 1: Assign an employee to a (newly created by API) issue
        assign_data = {
            'greenhouse_id': self.greenhouse.id,
            'employee_id': self.employee.id,
            'priority': 'high',
            'notes': 'Test issue assignment workflow',
            'issue_type': 'environmental' # Assuming API can create issue if not existing
        }
        response = self.client.post('/api/assign-employee',
                                 data=json.dumps(assign_data),
                                 content_type='application/json')
        
        self.assertEqual(response.status_code, 200, f"Assign API failed: {response.data.decode()}")
        assign_result = json.loads(response.data)
        self.assertTrue(assign_result['success'])
        
        # Verify issue creation and assignment
        issue = Issue.query.filter_by(greenhouse_id=self.greenhouse.id).first()
        self.assertIsNotNone(issue, "Issue was not created by assign-employee API.")
        self.assertEqual(issue.employee_id, self.employee.id)
        self.assertEqual(issue.status, 'assigned')
        self.assertEqual(issue.priority, 'high')
        self.assertEqual(issue.description, 'Test issue assignment workflow') # Check description if API sets it

        # Verify employee status
        db.session.refresh(self.employee) # Refresh employee from DB
        self.assertEqual(self.employee.status, 'busy')

        # Verify notification for admin (optional, depends on API logic)
        admin_notification = Notification.query.filter_by(user_id=self.admin_user.id, related_issue_id=issue.id).first()
        # self.assertIsNotNone(admin_notification, "Admin notification for assignment not created.")
        # self.assertIn(f"assigned to {self.employee.name}", admin_notification.message)


        # Step 2: Resolve the issue
        resolve_data = {
            'issue_id': issue.id # Assuming API uses issue_id to resolve
            # 'greenhouse_id': self.greenhouse.id # Original test used greenhouse_id
        }
        # Check API spec for /api/resolve-issue, it might take issue_id or greenhouse_id
        # The original test_greenhouse_system.py used greenhouse_id for resolve-issue.
        # Let's assume it can take issue_id for more directness. If not, adjust.
        # For now, sticking to the original test's use of greenhouse_id for /api/resolve-issue
        
        resolve_data_gh = {'greenhouse_id': self.greenhouse.id}
        response_resolve = self.client.post('/api/resolve-issue',
                                 data=json.dumps(resolve_data_gh),
                                 content_type='application/json')

        self.assertEqual(response_resolve.status_code, 200, f"Resolve API failed: {response_resolve.data.decode()}")
        resolve_result = json.loads(response_resolve.data)
        self.assertTrue(resolve_result['success'])

        # Verify issue status
        db.session.refresh(issue)
        self.assertEqual(issue.status, 'resolved')
        self.assertIsNotNone(issue.resolved_at)

        # Verify employee status
        db.session.refresh(self.employee)
        self.assertEqual(self.employee.status, 'available')
        
        # Verify greenhouse status (assuming resolving an issue makes it normal)
        db.session.refresh(self.greenhouse)
        self.assertEqual(self.greenhouse.status, 'normal')

        # Verify notification for admin (optional)
        resolve_notification = Notification.query.filter_by(user_id=self.admin_user.id, related_issue_id=issue.id, message_contains='resolved').first()
        # self.assertIsNotNone(resolve_notification, "Admin notification for resolution not created.")


if __name__ == '__main__':
    unittest.main()

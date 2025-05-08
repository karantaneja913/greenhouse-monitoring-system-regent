import unittest
from flask import session
from ..base_test import BaseTestCase, app # Import app for context
from models import db, User, Notification
from routes.utils import get_unread_notification_count, inject_global_vars
from datetime import datetime, timezone

class TestRoutesUtils(BaseTestCase):

    def test_get_unread_notification_count_no_user(self):
        # No user in session
        with app.test_request_context('/'): # Need a request context for session
            count = get_unread_notification_count()
            self.assertEqual(count, 0)

    def test_get_unread_notification_count_with_user_no_notifications(self):
        user = self._create_test_user(email="notifyuser@example.com")
        with app.test_request_context('/'): # Need a request context for session
            session['user_id'] = user.id # Simulate user login
            count = get_unread_notification_count()
            self.assertEqual(count, 0)

    def test_get_unread_notification_count_with_notifications(self):
        user = self._create_test_user(email="notifyuser2@example.com")
        
        # Create some notifications
        n1 = Notification(user_id=user.id, title="Test 1", message="Msg 1", is_read=False)
        n2 = Notification(user_id=user.id, title="Test 2", message="Msg 2", is_read=False)
        n3 = Notification(user_id=user.id, title="Test 3", message="Msg 3", is_read=True) # One read
        db.session.add_all([n1, n2, n3])
        db.session.commit()

        with app.test_request_context('/'): # Need a request context for session
            session['user_id'] = user.id # Simulate user login
            count = get_unread_notification_count()
            self.assertEqual(count, 2) # Expect 2 unread

    def test_inject_global_vars(self):
        user = self._create_test_user(email="globalvaruser@example.com")
        n1 = Notification(user_id=user.id, title="Global Test", message="Global Msg", is_read=False)
        db.session.add(n1)
        db.session.commit()

        with app.test_request_context('/'): # Need a request context for session
            session['user_id'] = user.id # Simulate user login
            
            global_vars = inject_global_vars()
            self.assertEqual(global_vars['unread_count'], 1)
            self.assertEqual(global_vars['current_year'], datetime.now(timezone.utc).year)

    def test_inject_global_vars_no_user(self):
         with app.test_request_context('/'): # Need a request context for session
            # Ensure session is clean for this test
            if 'user_id' in session:
                session.pop('user_id')
            
            global_vars = inject_global_vars()
            self.assertEqual(global_vars['unread_count'], 0)
            self.assertEqual(global_vars['current_year'], datetime.now(timezone.utc).year)


if __name__ == '__main__':
    unittest.main()

from flask import session, current_app
from datetime import datetime, timezone
from models import db, Notification # Import db and Notification from models

# Helper function to get unread count
def get_unread_notification_count():
    if 'user_id' in session:
        # Use the db object from the models module
        return Notification.query.filter_by(user_id=session['user_id'], is_read=False).count()
    return 0

# Inject unread count and current year into all templates
def inject_global_vars():
    return dict(
        unread_count=get_unread_notification_count(),
        current_year=datetime.now(timezone.utc).year # Use timezone-aware datetime
    )

# Function to register the context processor
def register_context_processors(app):
    app.context_processor(inject_global_vars)

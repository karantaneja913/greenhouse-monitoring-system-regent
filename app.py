import os
from flask import Flask
from config import config_by_name
from models import db # Import db instance from models.py
from routes.utils import register_context_processors # Import context processor registration function

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

    from routes.init_db import init_db_bp
    app.register_blueprint(init_db_bp)

    # Ensure the instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass # Already exists

    # Create database tables if they don't exist
    # This is usually done via Flask-Migrate in larger apps,
    # but for simplicity, we'll do it here on startup for dev.
    with app.app_context():
        db.create_all()

    return app

# Create the app instance for development run
app = create_app(os.getenv('FLASK_CONFIG') or 'default')

# Main application entry point for running with `python app.py`
if __name__ == '__main__':
    # Use the configuration setting for debug mode
    app.run(debug=app.config.get('DEBUG', True))

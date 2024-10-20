# app/__init__.py

from flask import Flask
from .routes import main
from .scheduler import init_app
import logging
import os

def create_app():
    """Create and configure the Flask application."""
    app = Flask(__name__, template_folder='../templates')  # Adjusted the template folder path
    app.secret_key = os.getenv('FLASK_SECRET_KEY', 'your_default_secret_key')  # Use a secure key in production

    # Register blueprints
    app.register_blueprint(main)

    # Initialize scheduler
    init_app(app)

    # Configure logging for Flask
    if not os.path.exists('logs'):
        os.makedirs('logs')
    handler = logging.FileHandler('logs/app.log')
    handler.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s:%(levelname)s:%(message)s')
    handler.setFormatter(formatter)
    app.logger.addHandler(handler)

    # Debugging: Print template search paths
    app.logger.info("Template search paths:")
    for path in app.jinja_loader.searchpath:
        app.logger.info(f" - {path}")

    return app

from flask import Flask
from flask_apscheduler import APScheduler
import logging
import os

def create_app():
    app = Flask(__name__)
    
    # Load configuration
    app.config.from_json(os.path.join('config', 'config.json'))
    
    # Initialize Scheduler
    scheduler = APScheduler()
    scheduler.init_app(app)
    scheduler.start()
    
    # Setup Logging
    logging.basicConfig(filename=os.path.join('logs', 'app.log'),
                        level=logging.INFO,
                        format='%(asctime)s %(levelname)s:%(message)s')
    
    # Import routes
    with app.app_context():
        from . import routes
        
    return app

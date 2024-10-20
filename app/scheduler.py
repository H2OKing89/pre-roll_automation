# app/scheduler.py

from apscheduler.schedulers.background import BackgroundScheduler
from .utils import check_and_update_preroll
import pytz
import logging

scheduler = BackgroundScheduler()

def init_app(app):
    """Initialize and start the scheduler."""
    # Use pytz to set the correct timezone (e.g., 'America/Chicago' for CDT)
    timezone = pytz.timezone('America/Chicago')  # Replace with your preferred timezone

    # Schedule the job with the proper timezone
    scheduler.add_job(func=check_and_update_preroll, trigger="cron", hour=0, minute=0, timezone=timezone)
    scheduler.start()
    app.logger.info("Scheduler started and job added.")

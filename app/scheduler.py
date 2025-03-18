from apscheduler.schedulers.background import BackgroundScheduler
from app.tasks import send_reminders  # Import after defining the scheduler
import logging

def start_reminder_scheduler():
    scheduler = BackgroundScheduler(daemon=True)
    scheduler.add_job(send_reminders, 'interval', minutes=1)  # Run every minute
    scheduler.start()
    logging.info("Reminder scheduler started.")

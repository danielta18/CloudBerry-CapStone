from apscheduler.schedulers.background import BackgroundScheduler
from app.tasks import send_reminders

def start_reminder_scheduler(app):
    scheduler = BackgroundScheduler()
    scheduler.add_job(send_reminders, 'interval', minutes=1, args=[app], coalesce=True, max_instances=1)
    scheduler.start()

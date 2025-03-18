import boto3
import pytz
from datetime import datetime
from botocore.exceptions import NoCredentialsError
from app.config import Config
from app.models import Reminder, User, Task, db
from app.email_utils import send_email
from flask import current_app

s3_client = boto3.client('s3')

def generate_presigned_url(file_key):
    try:
        url = s3_client.generate_presigned_url(
            'get_object',
            Params={'Bucket': Config.S3_BUCKET, 'Key': file_key},
            ExpiresIn=3600  
        )
        return url
    except NoCredentialsError:
        return None
    except Exception as e:
        print(f"ERROR: {e}")
        return None

def upload_file_to_s3(file, filename):
    try:
        s3_client.upload_fileobj(
            file, Config.S3_BUCKET, filename,
            ExtraArgs={"ACL": "private", "ContentType": file.content_type}
        )
        return filename  
    except NoCredentialsError:
        return None

def send_reminders(app):
    # Ensure you're in the app context
    with app.app_context():
        now_utc = datetime.now(pytz.utc)
        reminders = Reminder.query.filter(Reminder.reminder_time <= now_utc).all()

        for reminder in reminders:
            user = User.query.get(reminder.user_id)
            task = Task.query.get(reminder.task_id)

            # Log reminder details for debugging
            print(f"Processing reminder: {reminder.id} for task: {task.title if task else 'N/A'}")

            if user and user.email and task:
                send_email(user.email, "Task Reminder", f"Reminder: Your task '{task.title}' is due!")

                # Check if the reminder still exists before trying to delete it
                if db.session.object_session(reminder).is_modified:
                    db.session.delete(reminder)
                else:
                    print(f"Reminder {reminder.id} already deleted or not found.")

        db.session.commit()

from flask_mail import Message
from app.extensions import mail
from app.config import Config

def send_email(to, subject, body):
    try:
        msg = Message(subject, sender=Config.MAIL_DEFAULT_SENDER, recipients=[to])
        msg.body = body
        mail.send(msg)
        print(f"Reminder sent to {to}")
    except Exception as e:
        print(f"Failed to send email: {e}")
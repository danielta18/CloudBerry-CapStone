from flask_mail import Message
from app.extensions import mail

def send_email(to, subject, body):
    try:
        msg = Message(subject, sender="yourapp@example.com", recipients=[to])
        msg.body = body
        mail.send(msg)
        print(f"Reminder sent to {to}")
    except Exception as e:
        print(f"Failed to send email: {e}")
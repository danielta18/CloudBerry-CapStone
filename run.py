from app import create_app
from app.scheduler import start_reminder_scheduler

app = create_app()

start_reminder_scheduler(app)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
from flask import Blueprint, request, render_template, redirect, url_for, flash, send_file, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from app.extensions import db
from app.models import User, Task, Reminder
from app.tasks import upload_file_to_s3, generate_presigned_url, send_reminders
from urllib.parse import unquote
from datetime import datetime
from pytz import timezone as pytz_timezone

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
@login_required
def home():
    tasks = Task.query.filter_by(user_id=current_user.id).all()
    return render_template('index.html', tasks=tasks)

@main_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            login_user(user)
            return redirect(url_for('main.home'))
        flash('Invalid credentials')
    return render_template('login.html')

@main_bp.route('/upload/<int:task_id>', methods=['POST'])
@login_required
def upload_file(task_id):
    file = request.files['file']
    if file:
        filename = f"uploads/{current_user.id}/{task_id}_{datetime.utcnow().timestamp()}_{file.filename}"
        file_key = upload_file_to_s3(file, filename)

        if file_key:
            task = Task.query.get(task_id)
            task.attachment_key = file_key
            db.session.commit()
            flash("File uploaded successfully!")
    
    return redirect(url_for('main.home'))
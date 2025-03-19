from flask import Blueprint, request, render_template, redirect, url_for, flash, send_file, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from app.extensions import db
from app.models import User, Task, Reminder
from app.tasks import upload_file_to_s3, generate_presigned_url, send_reminders
from urllib.parse import unquote
from datetime import datetime
from pytz import timezone as pytz_timezone
from werkzeug.utils import secure_filename 
import time  

main_bp = Blueprint('main', __name__)

# --- Home route ---
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

@main_bp.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email'] 
        password = request.form['password']
        if User.query.filter_by(username=username).first() or User.query.filter_by(email=email).first():
            flash('Username or email already exists')
            return redirect(url_for('main.signup'))  
        new_user = User(username=username, email=email)
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.commit()
        login_user(new_user)
        return redirect(url_for('main.home'))  
    return render_template('signup.html')

@main_bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('main.login'))  

@main_bp.route('/')
@login_required
def home():
    tasks = Task.query.filter_by(user_id=current_user.id).all()
    uncompleted_tasks_count = sum(1 for task in tasks if not task.completed)
    task_added = request.args.get('task_added', False)
    return render_template('index.html', tasks=tasks, uncompleted_tasks_count=uncompleted_tasks_count, username=current_user.username, task_added=task_added)

@main_bp.route('/add', methods=['POST'])
@login_required
def add_task():
    title = request.form.get('title')
    new_task = Task(title=title, user_id=current_user.id)
    db.session.add(new_task)
    db.session.commit()
    return redirect(url_for('main.home', task_added=True))  

@main_bp.route('/delete/<int:task_id>')
@login_required
def delete_task(task_id):
    task = Task.query.filter_by(id=task_id, user_id=current_user.id).first()
    if task:
        db.session.delete(task)
        db.session.commit()
    return redirect(url_for('main.home'))  

@main_bp.route('/complete/<int:task_id>')
@login_required
def complete_task(task_id):
    task = Task.query.filter_by(id=task_id, user_id=current_user.id).first()
    if task:
        task.completed = True
        db.session.commit()
    return redirect(url_for('main.home'))  

@main_bp.route('/edit/<int:task_id>', methods=['GET', 'POST'])
@login_required
def edit_task(task_id):
    task = Task.query.filter_by(id=task_id, user_id=current_user.id).first()
    if not task:
        return redirect(url_for('main.home'))  
    if request.method == 'POST':
        task.title = request.form['title']
        db.session.commit()
        return redirect(url_for('main.home'))  
    return render_template('edit.html', task=task)

@main_bp.route('/upload/<int:task_id>', methods=['POST'])
@login_required
def upload_file(task_id):
    task = Task.query.filter_by(id=task_id, user_id=current_user.id).first()
    if not task:
        flash("Task not found")
        return redirect(url_for('main.home'))  

    file = request.files['file']
    if file:
        timestamp = int(time.time())  # Unique timestamp
        filename = f"uploads/{current_user.id}/{task_id}_{timestamp}_{secure_filename(file.filename)}"
        file_key = upload_file_to_s3(file, filename)

        if file_key:
            task.attachment_key = file_key  # Store file key instead of a direct URL
            db.session.commit()
            flash("File uploaded successfully!")
        else:
            flash("Error uploading file.")
    
    return redirect(url_for('main.home'))  

@main_bp.route('/view_attachment/<path:file_key>')
@login_required
def view_attachment(file_key):
    file_key = unquote(file_key)
    print(f"Requested file key: {file_key}")
    url = generate_presigned_url(file_key)

    print(f"Generated presigned URL: {url}")

    if url:
        print(f"Redirecting to: {url}")
        return redirect(url)  # Redirect user to the secure link
    else:
        flash("Error generating link. Try again.")
        return redirect(url_for('main.home'))  

@main_bp.route('/set_reminder', methods=['POST'])
@login_required
def set_reminder():
    data = request.get_json()
    task_id = data.get("task_id")
    tz = data.get("timezone")
    reminder_datetime = data.get("reminder_datetime")

    if not task_id or not tz or not reminder_datetime:
        return jsonify({"error": "Missing data"}), 400

    # Convert user-selected time to UTC
    local_tz = pytz_timezone(tz)
    local_time = datetime.strptime(reminder_datetime, "%Y-%m-%dT%H:%M")
    utc_time = local_tz.localize(local_time).astimezone(pytz_timezone("UTC"))

    # Save to DB
    new_reminder = Reminder(user_id=current_user.id, task_id=task_id, reminder_time=utc_time)
    db.session.add(new_reminder)
    db.session.commit()

    return jsonify({"message": "Reminder set!"}), 200

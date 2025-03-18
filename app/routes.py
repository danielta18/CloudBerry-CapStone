from flask import Blueprint, request, render_template, redirect, url_for, flash, send_file, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from app.extensions import db
from app.models import User, Task, Reminder
from app.tasks import upload_file_to_s3, generate_presigned_url, send_reminders
from urllib.parse import unquote
from datetime import datetime
from pytz import timezone as pytz_timezone

main_bp = Blueprint('main', __name__)

# --- Home route ---
@main_bp.route('/')
@login_required
def home():
    tasks = Task.query.filter_by(user_id=current_user.id).all()
    return render_template('index.html', tasks=tasks)

# --- Login route ---
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

# --- Signup route ---
@main_bp.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        email = request.form['email']

        if User.query.filter_by(username=username).first():
            flash('Username already exists')
        elif User.query.filter_by(email=email).first():
            flash('Email already exists')
        else:
            user = User(username=username, email=email)
            user.set_password(password)
            db.session.add(user)
            db.session.commit()
            flash('Account created successfully')
            return redirect(url_for('main.login'))

    return render_template('signup.html')

# --- Logout route ---
@main_bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('main.login'))

# --- Add Task Route ---
@main_bp.route('/add', methods=['POST'])
@login_required
def add_task():
    """ Add new task """
    title = request.form['title']
    description = request.form.get('description', '')

    new_task = Task(
        title=title,
        description=description,
        user_id=current_user.id
    )
    db.session.add(new_task)
    db.session.commit()
    flash('Task added successfully!')
    return redirect(url_for('main.home'))

# --- Edit Task Route ---
@main_bp.route('/edit/<int:task_id>', methods=['GET', 'POST'])
@login_required
def edit_task(task_id):
    """ Edit an existing task """
    task = Task.query.get_or_404(task_id)

    if request.method == 'POST':
        task.title = request.form['title']
        task.description = request.form.get('description', '')
        db.session.commit()
        flash('Task updated successfully!')
        return redirect(url_for('main.home'))

    return render_template('edit.html', task=task)

@main_bp.route('/complete/<int:task_id>')
@login_required
def complete_task(task_id):
    task = Task.query.filter_by(id=task_id, user_id=current_user.id).first()
    if task:
        task.completed = True
        db.session.commit()
    return redirect(url_for('home'))

# --- Delete Task Route ---
@main_bp.route('/delete/<int:task_id>', methods=['POST'])
@login_required
def delete_task(task_id):
    """ Delete a task """
    task = Task.query.get_or_404(task_id)
    
    if task.user_id != current_user.id:
        flash("Unauthorized action.")
        return redirect(url_for('main.home'))

    db.session.delete(task)
    db.session.commit()
    flash('Task deleted successfully!')
    return redirect(url_for('main.home'))

# --- Upload file route ---
@main_bp.route('/upload/<int:task_id>', methods=['POST'])
@login_required
def upload_file(task_id):
    """ Upload a file and attach it to a task """
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
        return redirect(url_for('home'))

# --- Download file route ---
@main_bp.route('/download/<int:task_id>')
@login_required
def download_file(task_id):
    """ Generate a presigned URL to download the file """
    task = Task.query.get_or_404(task_id)

    if task.attachment_key:
        presigned_url = generate_presigned_url(task.attachment_key)
        if presigned_url:
            return redirect(presigned_url)
        else:
            flash('Failed to generate download link.')
    else:
        flash('No file attached.')

    return redirect(url_for('main.home'))

# --- Set Reminder Route ---
@main_bp.route('/set_reminder/<int:task_id>', methods=['POST'])
@login_required
def set_reminder(task_id):
    """ Set reminder for a task """
    task = Task.query.get_or_404(task_id)
    
    reminder_time_str = request.form['reminder_time']
    timezone_str = request.form['timezone']

    try:
        local_tz = pytz_timezone(timezone_str)
        local_time = datetime.strptime(reminder_time_str, "%Y-%m-%dT%H:%M")
        local_time = local_tz.localize(local_time)
        utc_time = local_time.astimezone(pytz_timezone('UTC'))

        reminder = Reminder(task_id=task_id, reminder_time=utc_time)
        db.session.add(reminder)
        db.session.commit()

        flash('Reminder set successfully!')

    except Exception as e:
        flash(f'Error setting reminder: {str(e)}')

    return redirect(url_for('main.home'))

# --- Backup Route ---
@main_bp.route('/backup')
@login_required
def backup():
    """ Backup all tasks to a text file """
    import os

    tasks = Task.query.filter_by(user_id=current_user.id).all()
    backup_dir = 'backup'
    os.makedirs(backup_dir, exist_ok=True)

    backup_file = os.path.join(backup_dir, f"backup_{current_user.id}.txt")

    with open(backup_file, 'w') as f:
        for task in tasks:
            f.write(f"Title: {task.title}\n")
            f.write(f"Description: {task.description}\n")
            f.write(f"Created At: {task.created_at}\n")
            f.write("\n---\n\n")

    return send_file(backup_file, as_attachment=True)

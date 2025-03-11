from flask import Flask, request, render_template, redirect, url_for, flash, send_file
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from botocore.exceptions import NoCredentialsError
import boto3
import os
import time


app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Change this to a secure key

basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://admin:Work135!@cloudberry-capstone.c4du0i2ucqyz.us-east-1.rds.amazonaws.com/mydb'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

S3_BUCKET = "cloudberrycapstone"
S3_REGION = "us-east-1"
s3_client = boto3.client('s3')

def generate_presigned_url(file_key):
    try:
        url = s3_client.generate_presigned_url(
            'get_object',
            Params={'Bucket': S3_BUCKET, 'Key': file_key},
            ExpiresIn=3600  # Link expires in 1 hour
        )
        return url
    except NoCredentialsError:
        return None
    

def upload_file_to_s3(file, filename):
    """Uploads a file to S3 and returns the file key (not a public URL)"""
    try:
        s3_client.upload_fileobj(
            file, S3_BUCKET, filename,
            ExtraArgs={"ACL": "private", "ContentType": file.content_type}
        )
        return filename  # Return file key instead of S3 URL
    except NoCredentialsError:
        return None


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    title = db.Column(db.String(100), nullable=False)
    completed = db.Column(db.Boolean, default=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    attachment_key = db.Column(db.String(255), nullable=True)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            login_user(user)
            return redirect(url_for('home'))
        flash('Invalid credentials')
    return render_template('login.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if User.query.filter_by(username=username).first():
            flash('Username already exists')
            return redirect(url_for('signup'))
        new_user = User(username=username)
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.commit()
        login_user(new_user)
        return redirect(url_for('home'))
    return render_template('signup.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/')
@login_required
def home():
    tasks = Task.query.filter_by(user_id=current_user.id).all()
    uncompleted_tasks_count = sum(1 for task in tasks if not task.completed)
    task_added = request.args.get('task_added', False)
    return render_template('index.html', tasks=tasks, uncompleted_tasks_count=uncompleted_tasks_count, username=current_user.username, task_added=task_added)

@app.route('/add', methods=['POST'])
@login_required
def add_task():
    title = request.form.get('task')
    new_task = Task(title=title, user_id=current_user.id)
    db.session.add(new_task)
    db.session.commit()
    return redirect(url_for('home', task_added=True))

@app.route('/delete/<int:task_id>')
@login_required
def delete_task(task_id):
    task = Task.query.filter_by(id=task_id, user_id=current_user.id).first()
    if task:
        db.session.delete(task)
        db.session.commit()
    return redirect(url_for('home'))

@app.route('/complete/<int:task_id>')
@login_required
def complete_task(task_id):
    task = Task.query.filter_by(id=task_id, user_id=current_user.id).first()
    if task:
        task.completed = True
        db.session.commit()
    return redirect(url_for('home'))

@app.route('/edit/<int:task_id>', methods=['GET', 'POST'])
@login_required
def edit_task(task_id):
    task = Task.query.filter_by(id=task_id, user_id=current_user.id).first()
    if not task:
        return redirect(url_for('home'))
    if request.method == 'POST':
        task.title = request.form['title']
        db.session.commit()
        return redirect(url_for('home'))
    return render_template('edit.html', task=task)

@app.route('/upload/<int:task_id>', methods=['POST'])
@login_required
def upload_file(task_id):
    task = Task.query.filter_by(id=task_id, user_id=current_user.id).first()
    if not task:
        flash("Task not found")
        return redirect(url_for('home'))

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
    
    return redirect(url_for('home'))


@app.route('/view_attachment/<file_key>')
@login_required
def view_attachment(file_key):
    url = generate_presigned_url(file_key)
    if url:
        return redirect(url)  # Redirect user to the secure link
    else:
        flash("Error generating link. Try again.")
        return redirect(url_for('home'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(host='0.0.0.0', port=5000, debug=True)
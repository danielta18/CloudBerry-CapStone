import os

class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "your_secret_key")
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL", "mysql://admin:Work135!@cloudberry-capstone.c4du0i2ucqyz.us-east-1.rds.amazonaws.com/mydb")
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # S3 Configuration
    S3_BUCKET = "cloudberrycapstone"
    S3_REGION = "us-east-1"

    # Flask-Mail Configuration
    MAIL_SERVER = 'smtp.gmail.com'
    MAIL_PORT = 587
    MAIL_USE_TLS = True
    MAIL_USERNAME = "todolistreminders2025@gmail.com"
    MAIL_PASSWORD = "wbez wpay fytu kklf"  # Ensure this is the correct password with spaces
    MAIL_DEFAULT_SENDER = "todolistreminders2025@gmail.com"
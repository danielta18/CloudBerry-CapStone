from flask import Flask
from app.config import Config
from app.extensions import db, migrate, login_manager, mail
from app.routes import main_bp

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    mail.init_app(app)

    # Register blueprints
    app.register_blueprint(main_bp)

    return app
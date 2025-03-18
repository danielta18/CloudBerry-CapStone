from flask import Flask
from app.config import Config
from app.extensions import db, migrate, login_manager, mail
from app.routes import main_bp
from app.models import User  # Import User model here for user_loader

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    mail.init_app(app)

    # Add user_loader function
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))  # Use the User model here

    # Register blueprints
    app.register_blueprint(main_bp)

    return app
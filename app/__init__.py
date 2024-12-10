from flask import Flask
from app.models import db, init_models
import os


def create_app(config_class=None):
    app = Flask(__name__)

    # Load config
    if config_class is None:
        from app.config import Config
        config_class = Config

    app.config.from_object(config_class)

    # Ensure upload directories exist
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    os.makedirs(app.config['SUBMISSION_FOLDER'], exist_ok=True)

    # Initialize extensions
    db.init_app(app)

    with app.app_context():
        # Initialize models
        init_models()

        # Import routes after models are initialized
        from app.routes import admin_bp, api_bp

        # Register blueprints
        app.register_blueprint(admin_bp, url_prefix='/admin')
        app.register_blueprint(api_bp, url_prefix='/api')

        # Create database tables
        db.create_all()

    return app

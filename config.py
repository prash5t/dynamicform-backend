import os
from datetime import timedelta


class Config:
    # Base directory of the project
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))

    # SQLite database
    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(BASE_DIR, 'forms.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Upload folder for JSON files
    UPLOAD_FOLDER = os.path.join(BASE_DIR, 'app', 'uploaded_json_structure')

    # Secret key for session management
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'your-secret-key-here'

    # Maximum file size (3MB)
    MAX_CONTENT_LENGTH = 3 * 1024 * 1024

    # Allowed extensions for JSON files
    ALLOWED_EXTENSIONS = {'json'}

import os
import tempfile


class TestConfig:
    # Use temporary directory for uploads during testing
    UPLOAD_FOLDER = tempfile.mkdtemp()

    # Use in-memory SQLite database for testing
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Test secret key
    SECRET_KEY = 'test-secret-key'

    # Maximum file size (3MB)
    MAX_CONTENT_LENGTH = 3 * 1024 * 1024

    # Allowed extensions for JSON files
    ALLOWED_EXTENSIONS = {'json'}

    # Enable testing mode
    TESTING = True

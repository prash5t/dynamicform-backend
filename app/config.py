import os


class Config:
    # Base directory of the project
    BASE_DIR = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))

    # SQLite database
    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(BASE_DIR, 'forms.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Upload folder for JSON files
    UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploaded_json_structure')

    # Submission folder for form submissions
    SUBMISSION_FOLDER = os.path.join(BASE_DIR, 'uploaded_submissions')

    # Secret key for session management
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'your-secret-key-here'

    # Maximum file size (3MB)
    MAX_CONTENT_LENGTH = 3 * 1024 * 1024

    # Allowed extensions for JSON files
    ALLOWED_EXTENSIONS = {'json'}

    # Add new directory for uploaded documents
    UPLOADED_DOCUMENTS_DIR = os.path.join(BASE_DIR, 'uploaded_documents')

    # Update allowed extensions
    ALLOWED_PHOTO_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
    ALLOWED_FILE_EXTENSIONS = {'pdf', 'doc',
                               'docx', 'txt', 'png', 'jpg', 'jpeg'}

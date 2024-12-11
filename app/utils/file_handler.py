import os
import uuid
from werkzeug.utils import secure_filename
from flask import current_app


def get_file_extension(filename):
    """Get file extension without the dot, returns empty string if no extension"""
    try:
        # Split filename by dots and get the last part
        parts = filename.rsplit('.', 1)
        if len(parts) > 1:
            return parts[-1].lower()
        return ''
    except (IndexError, AttributeError):
        return ''


def is_allowed_file(filename):
    """Check if file extension is allowed, returns tuple (bool, str) with status and file type"""
    ext = get_file_extension(filename)
    if not ext:
        return False, "no extension"

    if ext in current_app.config['ALLOWED_PHOTO_EXTENSIONS']:
        return True, "photo"
    elif ext in current_app.config['ALLOWED_FILE_EXTENSIONS']:
        return True, "file"
    return False, ext


def save_uploaded_file(file):
    """
    Save uploaded file and return its relative path
    """
    try:
        # Get original filename and check extension before securing
        original_filename = file.filename
        if not original_filename:
            raise ValueError(f"Invalid filename: {file.filename}")

        # Check file extension using original filename
        is_allowed, file_type = is_allowed_file(original_filename)
        if not is_allowed:
            raise ValueError(
                f"File type not allowed: {file_type} (Original filename: {original_filename})")

        # Get extension from original filename
        ext = get_file_extension(original_filename)

        # Generate unique filename with the original extension
        unique_filename = f"{uuid.uuid4()}.{ext}"

        # Create upload directory if it doesn't exist
        upload_dir = current_app.config['UPLOADED_DOCUMENTS_DIR']
        os.makedirs(upload_dir, exist_ok=True)

        # Save file with unique filename
        file_path = os.path.join(upload_dir, unique_filename)
        file.save(file_path)

        # Return relative path from BASE_DIR
        return os.path.relpath(file_path, current_app.config['BASE_DIR'])

    except Exception as e:
        raise Exception(f"Failed to save file '{file.filename}': {str(e)}")

from flask import Blueprint, jsonify, current_app, request
import os
import json
from datetime import datetime
from app.models.form import Form
from app.models.submission import Submission
from app.models import db
import uuid
from app.utils.file_handler import save_uploaded_file

bp = Blueprint('api', __name__)


def create_error_response(message, field_errors=None):
    response = {
        'error': message
    }
    if field_errors:
        response['errors'] = field_errors
    return jsonify(response)


@bp.route('/forms', methods=['GET'])
def get_forms():
    try:
        forms = Form.query.all()
        return jsonify([form.to_dict() for form in forms])
    except Exception as e:
        return create_error_response(str(e)), 500


@bp.route('/forms/<form_id>', methods=['GET'])
def get_form(form_id):
    try:
        form = Form.query.get_or_404(form_id)
        file_path = os.path.join(
            current_app.config['UPLOAD_FOLDER'], form.formPath)

        if not os.path.exists(file_path):
            return create_error_response(
                'Form template file not found',
                [{'field': 'formPath', 'message': 'JSON file is missing'}]
            ), 404

        with open(file_path, 'r') as f:
            form_data = json.load(f)

        return jsonify(form_data)

    except Exception as e:
        return create_error_response(str(e)), 500


@bp.route('/forms/<form_id>/submit', methods=['POST'])
def submit_form(form_id):
    try:
        # Get the form
        form = Form.query.get_or_404(form_id)

        # Load form template
        template_path = os.path.join(
            current_app.config['UPLOAD_FOLDER'], form.formPath)
        with open(template_path, 'r') as f:
            template = json.load(f)

        # Get submission data
        submission_data = request.get_json()
        if not submission_data:
            return create_error_response('No submission data provided'), 400

        # Debug print
        print("Received submission data:", submission_data)

        # Validate submission
        is_valid, error_message = validate_submission(
            template, submission_data)
        if not is_valid:
            return create_error_response(f'Invalid submission: {error_message}'), 400

        # Get all file/photo fields from template
        file_fields = set()
        for page in template['pages']:
            for field in page['fields']:
                if field['type'] in ['file', 'photo']:
                    file_fields.add(field['key'])

        # Verify file paths exist only for file/photo fields
        for key, value in submission_data.items():
            if key in file_fields and isinstance(value, list) and value:
                print(f"Checking file paths for field {key}:", value)
                for path in value:
                    # Check if path exists relative to BASE_DIR
                    full_path = os.path.join(
                        current_app.config['BASE_DIR'], path)
                    print(f"Checking path: {path}")
                    print(f"Full path: {full_path}")
                    print(f"Path exists: {os.path.exists(full_path)}")
                    if not os.path.exists(full_path):
                        return create_error_response(f'File not found: {path}'), 400

        # Generate submission ID and save
        submission_id = str(uuid.uuid4())
        submission_path = f"{submission_id}.json"
        file_path = os.path.join(
            current_app.config['SUBMISSION_FOLDER'], submission_path)

        # Save submission data
        os.makedirs(current_app.config['SUBMISSION_FOLDER'], exist_ok=True)
        with open(file_path, 'w') as f:
            json.dump(submission_data, f, indent=2)

        # Create submission record
        submission = Submission(
            submissionId=submission_id,
            formId=form_id,
            submissionPath=submission_path
        )
        db.session.add(submission)
        db.session.commit()

        return jsonify({
            'message': 'Form submitted successfully',
            'submission': submission.to_dict()
        }), 201

    except Exception as e:
        db.session.rollback()
        return create_error_response(str(e)), 500


def validate_submission(template, submission_data):
    """Validate submission data against form template."""
    try:
        # Collect all required fields from template
        required_fields = {}
        for page in template['pages']:
            for field in page['fields']:
                if field.get('validation', {}).get('required', False):
                    # Skip if field has dependency and condition isn't met
                    if 'dependency' in field:
                        dep_field = field['dependency']['field']
                        dep_value = field['dependency']['value']
                        if submission_data.get(dep_field) != dep_value:
                            continue
                    required_fields[field['key']] = field

        # Check required fields
        for key, field in required_fields.items():
            if key not in submission_data:
                return False, f"Missing required field: {field['label']}"

            value = submission_data[key]
            if value is None:  # Skip validation for null values in non-required fields
                continue

            validation = field.get('validation', {})

            # Type validation
            if field['type'] == 'text':
                if not isinstance(value, str):
                    return False, f"Field '{field['label']}' must be text"
                if 'minLength' in validation and len(value) < validation['minLength']:
                    return False, f"Field '{field['label']}' is too short"

            elif field['type'] in ['radio', 'dropdown']:
                valid_values = [opt['value'] for opt in field['options']]
                if value not in valid_values:
                    return False, f"Invalid value for field '{field['label']}'"

            elif field['type'] == 'date':
                try:
                    from datetime import datetime
                    date_value = datetime.strptime(value, '%Y-%m-%d')

                    if 'startDate' in validation:
                        start_date = datetime.strptime(
                            validation['startDate'].split('T')[0], '%Y-%m-%d')
                        if date_value < start_date:
                            return False, f"Date in field '{field['label']}' is before allowed range"

                    if 'endDate' in validation:
                        end_date = datetime.strptime(
                            validation['endDate'].split('T')[0], '%Y-%m-%d')
                        if date_value > end_date:
                            return False, f"Date in field '{field['label']}' is after allowed range"

                except ValueError:
                    return False, f"Invalid date format in field '{field['label']}'. Use YYYY-MM-DD format"

            elif field['type'] in ['file', 'photo']:
                # Both file and photo fields should be lists of file paths
                if not isinstance(value, list):
                    return False, f"Field '{field['label']}' must be a list of file paths"

                for path in value:
                    if not isinstance(path, str):
                        return False, f"File paths in field '{field['label']}' must be strings"
                    # Ensure it's a raw file path
                    if path.startswith('http://') or path.startswith('https://'):
                        return False, f"Field '{field['label']}' must contain raw file paths, not URLs"

                # Check count constraints if specified
                if 'minCount' in validation and len(value) < validation['minCount']:
                    return False, f"Field '{field['label']}' requires at least {validation['minCount']} files"
                if 'maxCount' in validation and len(value) > validation['maxCount']:
                    return False, f"Field '{field['label']}' cannot have more than {validation['maxCount']} files"

        return True, None

    except Exception as e:
        return False, f"Validation error: {str(e)}"


@bp.route('/upload', methods=['POST'])
def upload_file():
    """
    Handle file upload and return stored path
    """
    try:
        if 'file' not in request.files:
            return create_error_response('No file part in the request'), 400

        file = request.files['file']
        if file.filename == '':
            return create_error_response('No file selected'), 400

        try:
            relative_path = save_uploaded_file(file)

            return jsonify({
                'message': 'File uploaded successfully',
                'uploadedPath': relative_path
            }), 201

        except ValueError as ve:
            return create_error_response(str(ve)), 400
        except Exception as e:
            return create_error_response(f"File upload failed: {str(e)}"), 500

    except Exception as e:
        return create_error_response(
            f"Upload request failed: {str(e)} (Content-Type: {request.content_type})"
        ), 500

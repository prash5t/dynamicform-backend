from flask import Blueprint, jsonify, current_app, request
import os
import json
from app.models.form import Form
from app.models.submission import Submission
from app.models import db

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

        # Load the form template
        template_path = os.path.join(
            current_app.config['UPLOAD_FOLDER'], form.formPath)
        if not os.path.exists(template_path):
            return create_error_response('Form template not found'), 404

        with open(template_path, 'r') as f:
            template = json.load(f)

        # Get submission data
        submission_data = request.get_json()
        if not submission_data:
            return create_error_response('No submission data provided'), 400

        # Validate submission against template
        is_valid, error_message = validate_submission(
            template, submission_data)
        if not is_valid:
            return create_error_response(f'Invalid submission: {error_message}'), 400

        # Create submissions directory if it doesn't exist
        os.makedirs(current_app.config['SUBMISSION_FOLDER'], exist_ok=True)

        # Create submission record
        submission = Submission(formId=form_id)
        db.session.add(submission)

        # Save submission data
        filename = f"{submission.submissionId}.json"
        file_path = os.path.join(
            current_app.config['SUBMISSION_FOLDER'], filename)

        with open(file_path, 'w') as f:
            json.dump(submission_data, f, indent=2)

        submission.submissionPath = filename
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
            validation = field.get('validation', {})

            # Type validation
            if field['type'] == 'text':
                if not isinstance(value, str):
                    return False, f"Field '{field['label']}' must be text"
                if 'minLength' in validation and len(value) < validation['minLength']:
                    return False, f"Field '{field['label']}' is too short"
                if 'maxLength' in validation and len(value) > validation['maxLength']:
                    return False, f"Field '{field['label']}' is too long"

            elif field['type'] in ['radio', 'dropdown']:
                valid_values = [opt['value'] for opt in field['options']]
                if value not in valid_values:
                    return False, f"Invalid value for field '{field['label']}'"

            elif field['type'] == 'date':
                try:
                    date_value = datetime.fromisoformat(
                        value.replace('Z', '+00:00'))
                    if 'startDate' in validation:
                        start_date = datetime.fromisoformat(
                            validation['startDate'].replace('Z', '+00:00'))
                        if date_value < start_date:
                            return False, f"Date in field '{field['label']}' is before allowed range"
                    if 'endDate' in validation:
                        end_date = datetime.fromisoformat(
                            validation['endDate'].replace('Z', '+00:00'))
                        if date_value > end_date:
                            return False, f"Date in field '{field['label']}' is after allowed range"
                except ValueError:
                    return False, f"Invalid date format in field '{field['label']}'"

        return True, None

    except Exception as e:
        return False, f"Validation error: {str(e)}"

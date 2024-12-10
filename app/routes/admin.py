from flask import Blueprint, render_template, request, jsonify, current_app
from werkzeug.utils import secure_filename
import os
import json
from app.models.form import Form
from app.models.submission import Submission
from app.models import db
import uuid

bp = Blueprint('admin', __name__)


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower(
           ) in current_app.config['ALLOWED_EXTENSIONS']


def validate_json_structure(json_data):
    # Check for required top-level fields
    required_fields = {'formName', 'pages'}
    missing_fields = required_fields - set(json_data.keys())
    if missing_fields:
        return False, f"Missing required top-level fields: {', '.join(missing_fields)}"

    if not isinstance(json_data['pages'], list):
        return False, "'pages' must be an array, got {type(json_data['pages']).__name__} instead"

    for page_index, page in enumerate(json_data['pages'], 1):
        # Check page structure
        required_page_fields = {'title', 'fields'}
        missing_page_fields = required_page_fields - set(page.keys())
        if missing_page_fields:
            return False, f"Page {page_index} is missing required fields: {', '.join(missing_page_fields)}"

        if not isinstance(page['fields'], list):
            return False, f"'fields' in page {page_index} must be an array, got {type(page['fields']).__name__} instead"

        # Validate each field in the page
        for field_index, field in enumerate(page['fields'], 1):
            required_field_attrs = {'key', 'type', 'label'}
            missing_field_attrs = required_field_attrs - set(field.keys())
            if missing_field_attrs:
                return False, f"Field {field_index} in page {page_index} is missing required attributes: {', '.join(missing_field_attrs)}"

            # Validate field type
            valid_field_types = {'text', 'number', 'date',
                                 'dropdown', 'radio', 'checkbox', 'file', 'photo'}
            if field['type'] not in valid_field_types:
                return False, f"Invalid field type '{field['type']}' for field '{field['key']}' in page {page_index}. Valid types are: {', '.join(valid_field_types)}"

            # Validate validation rules if present
            if 'validation' in field:
                if not isinstance(field['validation'], dict):
                    return False, f"'validation' for field '{field['key']}' in page {page_index} must be an object"

                # Validate specific rules based on field type
                if field['type'] in {'text', 'number'}:
                    if 'minLength' in field['validation'] and not isinstance(field['validation']['minLength'], int):
                        return False, f"'minLength' for field '{field['key']}' must be an integer"
                    if 'maxLength' in field['validation'] and not isinstance(field['validation']['maxLength'], int):
                        return False, f"'maxLength' for field '{field['key']}' must be an integer"

                elif field['type'] in {'dropdown', 'radio'}:
                    if 'options' not in field:
                        return False, f"Field '{field['key']}' of type '{field['type']}' must have 'options' array"
                    if not isinstance(field.get('options', []), list):
                        return False, f"'options' for field '{field['key']}' must be an array"
                    for option_index, option in enumerate(field.get('options', []), 1):
                        if not isinstance(option, dict) or 'display' not in option or 'value' not in option:
                            return False, f"Option {option_index} in field '{field['key']}' must have 'display' and 'value' properties"

                elif field['type'] in {'file', 'photo'}:
                    if 'maxSizeInMB' in field['validation'] and not isinstance(field['validation']['maxSizeInMB'], (int, float)):
                        return False, f"'maxSizeInMB' for field '{field['key']}' must be a number"

    return True, None


def create_error_response(message, field_errors=None):
    response = {
        'error': message
    }
    if field_errors:
        response['errors'] = field_errors
    return jsonify(response)


@bp.route('/', methods=['GET'])
def index():
    forms = Form.query.all()
    return render_template('admin/index.html', forms=forms)


@bp.route('/forms', methods=['POST'])
def add_form():
    if 'file' not in request.files:
        return create_error_response(
            'No file provided',
            [{'field': 'file', 'message': 'File is required'}]
        ), 400

    file = request.files['file']
    form_name = request.form.get('formName')

    if not form_name:
        return create_error_response(
            'Form name is required',
            [{'field': 'formName', 'message': 'Form name is required'}]
        ), 400

    if file.filename == '':
        return create_error_response(
            'No selected file',
            [{'field': 'file', 'message': 'Please select a file'}]
        ), 400

    if not allowed_file(file.filename):
        return create_error_response(
            'Invalid file type. Only JSON files are allowed',
            [{'field': 'file', 'message': 'Only JSON files are allowed'}]
        ), 400

    try:
        # Read the file content as string first
        file_content = file.read().decode('utf-8')

        try:
            # Try to parse the JSON
            json_data = json.loads(file_content)
        except json.JSONDecodeError as e:
            return create_error_response(
                'Invalid JSON format',
                [{'field': 'file', 'message': f'JSON parsing error: {str(e)}'}]
            ), 400

        # Validate JSON structure
        is_valid, error_message = validate_json_structure(json_data)

        if not is_valid:
            return create_error_response(
                f'Invalid JSON structure: {error_message}',
                [{'field': 'file', 'message': error_message}]
            ), 400

        # Generate form ID first
        form_id = str(uuid.uuid4())

        # Create the upload directory if it doesn't exist
        os.makedirs(current_app.config['UPLOAD_FOLDER'], exist_ok=True)

        # Save the JSON file with form ID
        filename = f"{form_id}.json"
        file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)

        # Write the validated JSON to file
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(json_data, f, indent=2)

        try:
            # Create form record in database with the file path
            form = Form(formId=form_id, formName=form_name, formPath=filename)
            db.session.add(form)
            db.session.commit()

            return jsonify({
                'message': 'Form added successfully',
                'form': form.to_dict()
            }), 201

        except Exception as db_error:
            # If database operation fails, clean up the saved file
            os.remove(file_path)
            raise db_error

    except UnicodeDecodeError:
        return create_error_response(
            'Invalid file encoding',
            [{'field': 'file', 'message': 'File must be UTF-8 encoded'}]
        ), 400
    except Exception as e:
        return create_error_response(str(e)), 500


@bp.route('/forms/<form_id>', methods=['DELETE'])
def delete_form(form_id):
    try:
        form = Form.query.get_or_404(form_id)

        # Delete JSON file
        file_path = os.path.join(
            current_app.config['UPLOAD_FOLDER'], form.formPath)
        if os.path.exists(file_path):
            os.remove(file_path)

        # Delete database record
        db.session.delete(form)
        db.session.commit()

        return jsonify({'message': 'Form deleted successfully'}), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@bp.route('/forms/<form_id>/view', methods=['GET'])
def view_form(form_id):
    try:
        form = Form.query.get_or_404(form_id)
        file_path = os.path.join(
            current_app.config['UPLOAD_FOLDER'], form.formPath)

        if not os.path.exists(file_path):
            return render_template('admin/error.html',
                                   message='Form template file not found')

        with open(file_path, 'r') as f:
            form_data = json.load(f)

        return render_template('admin/view_form.html',
                               form=form,
                               form_data=json.dumps(form_data, indent=2))

    except Exception as e:
        return render_template('admin/error.html',
                               message=f'Error loading form: {str(e)}')


@bp.route('/forms/<form_id>/submissions')
def list_submissions(form_id):
    try:
        form = Form.query.get_or_404(form_id)
        submissions = Submission.query.filter_by(formId=form_id)\
            .order_by(Submission.submittedDate.desc()).all()
        return render_template('admin/submissions.html', form=form, submissions=submissions)
    except Exception as e:
        return render_template('admin/error.html', message=str(e))


@bp.route('/submissions/<submission_id>/view')
def view_submission(submission_id):
    try:
        submission = Submission.query.get_or_404(submission_id)

        # Get the submission data file path
        file_path = os.path.join(
            current_app.config['SUBMISSION_FOLDER'],
            submission.submissionPath
        )

        if not os.path.exists(file_path):
            return render_template('admin/error.html',
                                   message='Submission data file not found')

        # Read the submission data
        with open(file_path, 'r') as f:
            submission_data = json.load(f)

        return render_template('admin/view_submission.html',
                               submission=submission,
                               submission_data=json.dumps(submission_data, indent=2))

    except Exception as e:
        return render_template('admin/error.html', message=str(e))


@bp.route('/submissions/<submission_id>', methods=['DELETE'])
def delete_submission(submission_id):
    try:
        submission = Submission.query.get_or_404(submission_id)

        # Delete the submission file
        file_path = os.path.join(
            current_app.config['SUBMISSION_FOLDER'],
            submission.submissionPath
        )
        if os.path.exists(file_path):
            os.remove(file_path)

        # Delete database record
        db.session.delete(submission)
        db.session.commit()

        return jsonify({'message': 'Submission deleted successfully'})

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

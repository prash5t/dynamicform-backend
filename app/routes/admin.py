from flask import Blueprint, render_template, request, jsonify, current_app
from werkzeug.utils import secure_filename
import os
import json
from app.models import db, Form

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
        # Validate JSON structure
        json_data = json.load(file)
        is_valid, error_message = validate_json_structure(json_data)

        if not is_valid:
            return create_error_response(
                f'Invalid JSON structure: {error_message}',
                [{'field': 'file', 'message': error_message}]
            ), 400

        # Create form record in database
        form = Form(form_name=form_name, form_path='')
        db.session.add(form)

        # Save the JSON file with form ID
        filename = f"{form.formId}.json"
        file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)

        # Reset file pointer to beginning
        file.seek(0)
        file.save(file_path)

        # Update form path and commit
        form.formPath = filename
        db.session.commit()

        return jsonify({
            'message': 'Form added successfully',
            'form': form.to_dict()
        }), 201

    except json.JSONDecodeError:
        return create_error_response(
            'Invalid JSON file',
            [{'field': 'file', 'message': 'File is not a valid JSON'}]
        ), 400
    except Exception as e:
        db.session.rollback()
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

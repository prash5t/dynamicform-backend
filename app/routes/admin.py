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
    required_fields = {'formName', 'pages'}
    if not all(field in json_data for field in required_fields):
        return False, "Missing required fields in JSON structure"

    if not isinstance(json_data['pages'], list):
        return False, "'pages' must be an array"

    for page in json_data['pages']:
        if 'title' not in page or 'fields' not in page:
            return False, "Each page must have 'title' and 'fields'"

        if not isinstance(page['fields'], list):
            return False, "'fields' must be an array"

    return True, None


@bp.route('/', methods=['GET'])
def index():
    forms = Form.query.all()
    return render_template('admin/index.html', forms=forms)


@bp.route('/forms', methods=['POST'])
def add_form():
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400

    file = request.files['file']
    form_name = request.form.get('formName')

    if not form_name:
        return jsonify({'error': 'Form name is required'}), 400

    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    if not allowed_file(file.filename):
        return jsonify({'error': 'Invalid file type. Only JSON files are allowed'}), 400

    try:
        # Validate JSON structure
        json_data = json.load(file)
        is_valid, error_message = validate_json_structure(json_data)

        if not is_valid:
            return jsonify({'error': f'Invalid JSON structure: {error_message}'}), 400

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
        return jsonify({'error': 'Invalid JSON file'}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


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

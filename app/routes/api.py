from flask import Blueprint, jsonify, current_app
import os
import json
from app.models import Form

bp = Blueprint('api', __name__)


@bp.route('/forms', methods=['GET'])
def get_forms():
    try:
        forms = Form.query.all()
        return jsonify([form.to_dict() for form in forms])
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@bp.route('/forms/<form_id>', methods=['GET'])
def get_form(form_id):
    try:
        form = Form.query.get_or_404(form_id)
        file_path = os.path.join(
            current_app.config['UPLOAD_FOLDER'], form.formPath)

        if not os.path.exists(file_path):
            return jsonify({'error': 'Form template file not found'}), 404

        with open(file_path, 'r') as f:
            form_data = json.load(f)

        return jsonify(form_data)

    except Exception as e:
        return jsonify({'error': str(e)}), 500

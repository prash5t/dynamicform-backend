import json
import io
from app.models import Form


def test_admin_index(client):
    """Test the admin dashboard page."""
    response = client.get('/admin/')
    assert response.status_code == 200
    assert b'Form Template Admin' in response.data


def test_add_form_success(client, sample_form_data):
    """Test successfully adding a new form."""
    data = {
        'formName': 'Test Form',
        'file': (io.BytesIO(json.dumps(sample_form_data).encode()), 'test.json')
    }

    response = client.post('/admin/forms',
                           data=data,
                           content_type='multipart/form-data')

    assert response.status_code == 201
    assert response.json['message'] == 'Form added successfully'
    assert 'formId' in response.json['form']


def test_add_form_invalid_json(client):
    """Test adding a form with invalid JSON."""
    data = {
        'formName': 'Test Form',
        'file': (io.BytesIO(b'invalid json'), 'test.json')
    }

    response = client.post('/admin/forms',
                           data=data,
                           content_type='multipart/form-data')

    assert response.status_code == 400
    assert 'Invalid JSON file' in response.json['error']


def test_delete_form(client, app, sample_form_data):
    """Test deleting a form."""
    # Create a test form
    with app.app_context():
        form = Form(form_name="Test Form", form_path="test.json")
        db.session.add(form)
        db.session.commit()
        form_id = form.formId

        # Save sample JSON
        with open(os.path.join(app.config['UPLOAD_FOLDER'], 'test.json'), 'w') as f:
            json.dump(sample_form_data, f)

    response = client.delete(f'/admin/forms/{form_id}')
    assert response.status_code == 200
    assert response.json['message'] == 'Form deleted successfully'

    # Verify form is deleted
    with app.app_context():
        assert Form.query.get(form_id) is None

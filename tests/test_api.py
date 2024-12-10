import json
import pytest
from app.models import Form


def test_get_forms_empty(client):
    """Test getting forms when database is empty."""
    response = client.get('/api/forms')
    assert response.status_code == 200
    assert response.json == []


def test_get_forms(client, app, sample_form_data):
    """Test getting forms after adding one."""
    # Create a test form
    with app.app_context():
        form = Form(form_name="Test Form", form_path="test.json")
        db.session.add(form)
        db.session.commit()
        form_id = form.formId

    response = client.get('/api/forms')
    assert response.status_code == 200
    assert len(response.json) == 1
    assert response.json[0]['formId'] == form_id
    assert response.json[0]['formName'] == "Test Form"


def test_get_form_by_id(client, app, sample_form_data):
    """Test getting a specific form by ID."""
    # Create a test form
    with app.app_context():
        form = Form(form_name="Test Form", form_path="test.json")
        db.session.add(form)
        db.session.commit()
        form_id = form.formId

        # Save sample JSON
        with open(os.path.join(app.config['UPLOAD_FOLDER'], 'test.json'), 'w') as f:
            json.dump(sample_form_data, f)

    response = client.get(f'/api/forms/{form_id}')
    assert response.status_code == 200
    assert response.json['formName'] == "Test Form"
    assert len(response.json['pages']) == 1


def test_get_nonexistent_form(client):
    """Test getting a form that doesn't exist."""
    response = client.get('/api/forms/nonexistent-id')
    assert response.status_code == 404

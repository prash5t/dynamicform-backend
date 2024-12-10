import pytest
import os
import json
from app import create_app, db
from tests.config import TestConfig


@pytest.fixture
def app():
    """Create and configure a new app instance for each test."""
    app = create_app(TestConfig)

    # Create the database and tables
    with app.app_context():
        db.create_all()

    yield app

    # Clean up
    with app.app_context():
        db.drop_all()


@pytest.fixture
def client(app):
    """A test client for the app."""
    return app.test_client()


@pytest.fixture
def sample_form_data():
    """Sample form data for testing."""
    return {
        "formName": "Test Form",
        "pages": [
            {
                "title": "Test Page",
                "fields": [
                    {
                        "key": "testField",
                        "type": "text",
                        "label": "Test Field"
                    }
                ]
            }
        ]
    }

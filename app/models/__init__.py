from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

# Models will be imported after db is initialized in create_app
Form = None
Submission = None


def init_models():
    # Import models here to avoid circular imports
    global Form, Submission

    if Form is None:
        from .form import Form
    if Submission is None:
        from .submission import Submission


__all__ = ['db', 'Form', 'Submission']

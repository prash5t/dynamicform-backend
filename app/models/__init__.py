from datetime import datetime
from app import db
import uuid


class Form(db.Model):
    __tablename__ = 'forms'

    formId = db.Column(db.String(36), primary_key=True)
    formName = db.Column(db.String(100), nullable=False)
    uploadedDate = db.Column(
        db.DateTime, nullable=False, default=datetime.utcnow)
    formPath = db.Column(db.String(255), nullable=False)

    def __init__(self, form_name, form_path):
        self.formId = str(uuid.uuid4())
        self.formName = form_name
        self.formPath = form_path

    def to_dict(self):
        return {
            'formId': self.formId,
            'formName': self.formName
        }

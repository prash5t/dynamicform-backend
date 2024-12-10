from datetime import datetime
import uuid
from . import db


class Form(db.Model):
    __tablename__ = 'forms'

    formId = db.Column(db.String(36), primary_key=True,
                       default=lambda: str(uuid.uuid4()))
    formName = db.Column(db.String(100), nullable=False)
    formPath = db.Column(db.String(255), nullable=False)
    uploadedDate = db.Column(
        db.DateTime, nullable=False, default=datetime.utcnow)

    def to_dict(self):
        return {
            'formId': self.formId,
            'formName': self.formName,
            'uploadedDate': self.uploadedDate.isoformat()
        }

from datetime import datetime
import uuid
from . import db


class Submission(db.Model):
    __tablename__ = 'submissions'

    submissionId = db.Column(
        db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    formId = db.Column(db.String(36), db.ForeignKey(
        'forms.formId'), nullable=False)
    submittedDate = db.Column(
        db.DateTime, nullable=False, default=datetime.utcnow)
    submissionPath = db.Column(db.String(255), nullable=False)

    # Relationship with Form
    form = db.relationship(
        'Form', backref=db.backref('submissions', lazy=True))

    def to_dict(self):
        return {
            'submissionId': self.submissionId,
            'formId': self.formId,
            'submittedDate': self.submittedDate.isoformat(),
            'form': {
                'formId': self.form.formId,
                'formName': self.form.formName
            }
        }

from app import db
from datetime import datetime

class Agreement(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    signature1 = db.Column(db.Text)
    signature2 = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    signed_at = db.Column(db.DateTime)

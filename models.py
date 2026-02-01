from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime
import uuid

db = SQLAlchemy()

class User(UserMixin, db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    secret_token = db.Column(db.String(120), unique=True, nullable=True)
    role = db.Column(db.String(20), default='user')
    can_upload = db.Column(db.Boolean, default=False)
    can_list_results = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime, nullable=True)

    def get_id(self):
        return str(self.id)

    def generate_token(self):
        """Generate a new secret token for the user"""
        self.secret_token = str(uuid.uuid4())
        return self.secret_token

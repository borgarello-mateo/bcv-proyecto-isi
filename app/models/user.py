from ..extensions import db

MAX_LENGTH = 120


class User(db.Model):
    email = db.Column(db.String(MAX_LENGTH), primary_key=True)
    password = db.Column(db.String(MAX_LENGTH), nullable=False)

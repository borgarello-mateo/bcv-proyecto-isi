from ..extensions import db

MAX_LENGTH = 80

class Categoria(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(MAX_LENGTH), unique=True, nullable=False)
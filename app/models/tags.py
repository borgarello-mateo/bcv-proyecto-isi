from ..extensions import db

MAX_LENGTH = 50


class Etiqueta(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(MAX_LENGTH), unique=True, nullable=False)

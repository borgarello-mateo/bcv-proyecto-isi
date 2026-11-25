from datetime import datetime, timezone
from ..extensions import db
from .user import MAX_LENGTH as MAX_EMAIL_LENGTH


# Clase abstracta, no se genera una tabla propia
class Respuesta(db.Model):
    __abstract__ = True

    id = db.Column(db.Integer, primary_key=True)
    id_pregunta = db.Column(
        db.Integer,
        db.ForeignKey("pregunta.id", ondelete="CASCADE"),
        nullable=False
    )
    cuerpo = db.Column(db.Text, nullable=False)
    fecha_creacion = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    aceptada = db.Column(
        db.Boolean,
        nullable=False,
        default=False
    )

# TODO: Agregar funcionalidad strategy
class RespuestaIA(Respuesta):
    __tablename__ = "respuesta_ia"

    pregunta =  db.relationship(
        "Pregunta",
        backref=db.backref("respuestas_ia", lazy=True, cascade="all"),
    )

class RespuestaHumano(Respuesta):
    __tablename__ = "respuesta_humano"

    email_autor = db.Column(
        db.String(MAX_EMAIL_LENGTH),
        db.ForeignKey("user.email", ondelete="CASCADE"),
        nullable=False
    )
    pregunta =  db.relationship(
        "Pregunta",
        backref=db.backref("respuestas_humano", lazy=True, cascade="all"),
    )
    autor = db.relationship(
        "User",
        backref=db.backref("respuestas", lazy=True)
    )

import re
from datetime import UTC, datetime

from ..extensions import db

MAX_TITULO_LEN = 150
MODOS_RESPUESTA = ("usuarios", "ia", "ambas")

pregunta_etiqueta = db.Table(
    "pregunta_etiqueta",
    db.Column(
        "pregunta_id",
        db.Integer,
        db.ForeignKey("pregunta.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    db.Column(
        "etiqueta_id",
        db.Integer,
        db.ForeignKey("etiqueta.id", ondelete="CASCADE"),
        primary_key=True,
    ),
)


def extraer_texto_plano_html(html_content: str | None) -> str:
    if not html_content:
        return ""
    sin_etiquetas = re.sub(r"<[^>]*>", " ", html_content)
    sin_entidades = sin_etiquetas.replace("&nbsp;", " ")
    return " ".join(sin_entidades.split()).strip()


class Pregunta(db.Model):
    __tablename__ = "pregunta"

    id = db.Column(db.Integer, primary_key=True)
    titulo = db.Column(db.String(MAX_TITULO_LEN), nullable=False)
    cuerpo = db.Column(db.Text, nullable=False)
    fecha_creacion = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
    )
    fecha_actualizacion = db.Column(
        db.DateTime(timezone=True),
        nullable=True,
    )
    categoria_id = db.Column(
        db.Integer,
        db.ForeignKey("categoria.id"),
        nullable=False,
    )
    autor_email = db.Column(
        db.String(120),
        db.ForeignKey("user.email"),
        nullable=False,
    )
    modo_respuesta = db.Column(
        db.String(20),
        nullable=False,
        default="ambas",
    )
    pendiente_respuesta_ia = db.Column(
        db.Boolean,
        nullable=False,
        default=False,
    )

    categoria = db.relationship(
        "Categoria",
        backref=db.backref("preguntas", lazy=True),
    )
    autor = db.relationship(
        "User",
        backref=db.backref("preguntas", lazy=True),
    )
    etiquetas = db.relationship(
        "Etiqueta",
        secondary=pregunta_etiqueta,
        lazy="subquery",
        backref=db.backref("preguntas", lazy=True),
    )

    @property
    def tiene_etiqueta_ia_help(self) -> bool:
        return any(
            (etiqueta.nombre or "").strip().lower() == "ia-help"
            for etiqueta in self.etiquetas
        )

    @property
    def supero_24h_sin_respuesta(self) -> bool:
        if not self.fecha_creacion:
            return False
        if self.respuestas_humano and self.modo_respuesta != "ambas":
            return False
        creacion = self.fecha_creacion
        if creacion.tzinfo is None:
            creacion = creacion.replace(tzinfo=UTC)
        horas = (datetime.now(UTC) - creacion).total_seconds() / 3600
        return horas >= 24

    def debe_activar_agente_ia(self) -> bool:
        if self.respuestas_humano and self.modo_respuesta != "ambas":
            return False
        return (
            self.modo_respuesta in ("ia", "ambas")
            or self.tiene_etiqueta_ia_help
            or self.supero_24h_sin_respuesta
        )

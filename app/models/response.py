from datetime import UTC, datetime

from ..extensions import db
from .user import MAX_LENGTH as MAX_EMAIL_LENGTH
from .question import Pregunta


# Clase abstracta, no se genera una tabla propia
class Respuesta(db.Model):
    __abstract__ = True

    id = db.Column(db.Integer, primary_key=True)
    id_pregunta = db.Column(
        db.Integer, db.ForeignKey("pregunta.id", ondelete="CASCADE"), nullable=False
    )
    cuerpo = db.Column(db.Text, nullable=False)
    fecha_creacion = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
    )
    aceptada = db.Column(db.Boolean, nullable=False, default=False)


class Strategy:
    nombre = "Strategy"

    def generar(self, pregunta: Pregunta) -> str:
        raise NotImplementedError("Debe implementar generar(pregunta)")


class StrategyOpenAI(Strategy):
    nombre = "OpenAI"

    def generar(self, pregunta: Pregunta) -> str:
        return f"<p><strong>[OpenAI]</strong> Respuesta simulada para <em>{pregunta.titulo}</em>.</p>"


class StrategyGemini(Strategy):
    nombre = "Gemini"

    def generar(self, pregunta: Pregunta) -> str:
        return f"<p><strong>[Gemini]</strong> Respuesta simulada para <em>{pregunta.titulo}</em>.</p>"


class StrategyModeloLocal(Strategy):
    nombre = "ModeloLocal"

    def generar(self, pregunta: Pregunta) -> str:
        return f"<p><strong>[Modelo Local]</strong> Respuesta simulada para <em>{pregunta.titulo}</em>.</p>"


ESTRATEGIAS = {
    "openai": StrategyOpenAI(),
    "gemini": StrategyGemini(),
    "modelo_local": StrategyModeloLocal(),
}


def obtener_strategy(clave: str | None) -> Strategy:
    if not clave:
        return ESTRATEGIAS["openai"]
    return ESTRATEGIAS.get(clave.strip().lower(), ESTRATEGIAS["openai"])


# TODO: Agregar funcionalidad strategy (hecho)
class RespuestaIA(Respuesta):
    __tablename__ = "respuesta_ia"

    pregunta = db.relationship(
        "Pregunta",
        backref=db.backref("respuestas_ia", lazy=True, cascade="all"),
    )

    def usar_strategy(self, strategy: Strategy) -> str:
        self.cuerpo = strategy.generar(self.pregunta)
        return self.cuerpo


class RespuestaHumano(Respuesta):
    __tablename__ = "respuesta_humano"

    email_autor = db.Column(
        db.String(MAX_EMAIL_LENGTH),
        db.ForeignKey("user.email", ondelete="CASCADE"),
        nullable=False,
    )
    pregunta = db.relationship(
        "Pregunta",
        backref=db.backref("respuestas_humano", lazy=True, cascade="all"),
    )
    autor = db.relationship("User", backref=db.backref("respuestas", lazy=True))


def generar_respuesta_ia_si_corresponde(
    pregunta: Pregunta, clave_estrategia: str | None = "openai"
) -> RespuestaIA | None:
    if not pregunta.debe_activar_agente_ia():
        pregunta.pendiente_respuesta_ia = False
        return None

    strategy = obtener_strategy(clave_estrategia)
    respuesta = RespuestaIA(id_pregunta=pregunta.id, cuerpo="", pregunta=pregunta)
    respuesta.usar_strategy(strategy)
    pregunta.pendiente_respuesta_ia = False
    db.session.add(respuesta)
    return respuesta

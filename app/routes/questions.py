from datetime import UTC, datetime
from functools import wraps

from flask import (
    Blueprint,
    abort,
    redirect,
    render_template,
    request,
    session,
    url_for,
)

from ..extensions import db
from ..models.category import Categoria
from ..models.question import (
    MAX_TITULO_LEN,
    MODOS_RESPUESTA,
    Pregunta,
    extraer_texto_plano_html,
)
from ..models.response import (
    RespuestaHumano,
    RespuestaIA,
    generar_respuesta_ia_si_corresponde,
)
from ..models.tags import Etiqueta
from ..models.user import User

bp = Blueprint("questions", __name__)


def _usuario_actual():
    email = session.get("user")
    if not email:
        return None
    return db.session.get(User, email)


def login_requerido(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        if not _usuario_actual():
            return redirect(url_for("auth.index_login"))
        return func(*args, **kwargs)

    return wrapper


def _render_formulario(
    error=None,
    form_data=None,
    selected_tag_ids=None,
    pregunta=None,
):
    categorias = Categoria.query.order_by(Categoria.nombre.asc()).all()
    etiquetas = Etiqueta.query.order_by(Etiqueta.nombre.asc()).all()
    form_action = (
        url_for("questions.editar_pregunta", pregunta_id=pregunta.id)
        if pregunta
        else url_for("questions.crear_pregunta")
    )
    return render_template(
        "create_question.html",
        categorias=categorias,
        etiquetas=etiquetas,
        error=error,
        form_data=form_data or {},
        selected_tag_ids=selected_tag_ids or set(),
        pregunta=pregunta,
        form_action=form_action,
    )


def _validar_y_parsear_payload(form):
    titulo = form.get("titulo", "").strip()
    cuerpo_html = form.get("cuerpo", "").strip()
    categoria_id_raw = form.get("categoria_id", "").strip()
    modo_respuesta = form.get("modo_respuesta", "ambas").strip().lower()
    tag_ids_raw = form.getlist("etiquetas")

    selected_tag_ids = {int(raw_id) for raw_id in tag_ids_raw if raw_id.isdigit()}

    form_data = {
        "titulo": titulo,
        "cuerpo": cuerpo_html,
        "categoria_id": categoria_id_raw,
        "modo_respuesta": modo_respuesta,
    }

    if not titulo:
        return None, "El título es obligatorio.", form_data, selected_tag_ids

    if len(titulo) > MAX_TITULO_LEN:
        return (
            None,
            f"El título no debe superar los {MAX_TITULO_LEN} caracteres.",
            form_data,
            selected_tag_ids,
        )

    texto_cuerpo = extraer_texto_plano_html(cuerpo_html)
    if not texto_cuerpo:
        return (
            None,
            "El cuerpo detallado de la pregunta es obligatorio.",
            form_data,
            selected_tag_ids,
        )

    if not categoria_id_raw.isdigit():
        return (
            None,
            "Debes seleccionar una categoría válida.",
            form_data,
            selected_tag_ids,
        )

    categoria = db.session.get(Categoria, int(categoria_id_raw))
    if not categoria:
        return (
            None,
            "La categoría seleccionada no existe.",
            form_data,
            selected_tag_ids,
        )

    if modo_respuesta not in MODOS_RESPUESTA:
        modo_respuesta = "ambas"

    etiquetas_seleccionadas = []
    if selected_tag_ids:
        etiquetas_seleccionadas = (
            Etiqueta.query.filter(Etiqueta.id.in_(selected_tag_ids))
            .order_by(Etiqueta.nombre.asc())
            .all()
        )

    payload = {
        "titulo": titulo,
        "cuerpo": cuerpo_html,
        "categoria_id": categoria.id,
        "modo_respuesta": modo_respuesta,
        "etiquetas": etiquetas_seleccionadas,
    }
    return payload, None, form_data, selected_tag_ids


@bp.get("/preguntas")
@login_requerido
def listar_preguntas():
    autor = _usuario_actual()
    preguntas = Pregunta.query.order_by(Pregunta.fecha_creacion.desc()).all()
    procesar_preguntas_vencidas_24h(preguntas)
    return render_template(
        "questions_list.html",
        preguntas=preguntas,
        user=autor.email,
    )


@bp.get("/preguntas/<int:pregunta_id>")
@login_requerido
def detalle_pregunta(pregunta_id: int):
    autor = _usuario_actual()
    pregunta = db.session.get(Pregunta, pregunta_id)
    if not pregunta:
        abort(404)

    procesar_preguntas_vencidas_24h([pregunta])

    respuestas_ia = sorted(
        pregunta.respuestas_ia, key=lambda r: r.fecha_creacion, reverse=True
    )

    respuestas_humano = sorted(
        pregunta.respuestas_humano, key=lambda r: r.fecha_creacion, reverse=True
    )

    tiene_respuestas = len(respuestas_ia) > 0 or len(respuestas_humano) > 0

    return render_template(
        "question_detail.html",
        pregunta=pregunta,
        user=autor.email,
        es_autor=(pregunta.autor_email == autor.email),
        respuestas_ia=respuestas_ia,
        respuestas_humano=respuestas_humano,
        tiene_respuestas=tiene_respuestas,
    )


@bp.get("/preguntas/nueva")
@login_requerido
def nueva_pregunta_form():
    return _render_formulario(
        form_data={"modo_respuesta": "ambas"},
    )


@bp.post("/preguntas")
@login_requerido
def crear_pregunta():
    autor = _usuario_actual()
    payload, error, form_data, selected_tag_ids = _validar_y_parsear_payload(
        request.form
    )

    if error:
        return _render_formulario(
            error=error,
            form_data=form_data,
            selected_tag_ids=selected_tag_ids,
        )

    estrategia_ia = request.form.get("estrategia_ia", "openai")

    pregunta = Pregunta(
        titulo=payload["titulo"],
        cuerpo=payload["cuerpo"],
        fecha_creacion=datetime.now(UTC),
        categoria_id=payload["categoria_id"],
        autor_email=autor.email,
        modo_respuesta=payload["modo_respuesta"],
        etiquetas=payload["etiquetas"],
    )

    db.session.add(pregunta)
    db.session.flush()
    generar_respuesta_ia_si_corresponde(pregunta, estrategia_ia)
    db.session.commit()

    return redirect(url_for("questions.detalle_pregunta", pregunta_id=pregunta.id))


@bp.get("/preguntas/<int:pregunta_id>/editar")
@login_requerido
def editar_pregunta_form(pregunta_id: int):
    autor = _usuario_actual()
    pregunta = db.session.get(Pregunta, pregunta_id)
    if not pregunta:
        abort(404)
    if pregunta.autor_email != autor.email:
        abort(403)

    form_data = {
        "titulo": pregunta.titulo,
        "cuerpo": pregunta.cuerpo,
        "categoria_id": str(pregunta.categoria_id),
        "modo_respuesta": pregunta.modo_respuesta,
    }
    selected_tag_ids = {tag.id for tag in pregunta.etiquetas}

    return _render_formulario(
        form_data=form_data,
        selected_tag_ids=selected_tag_ids,
        pregunta=pregunta,
    )


@bp.post("/preguntas/<int:pregunta_id>/editar")
@login_requerido
def editar_pregunta(pregunta_id: int):
    autor = _usuario_actual()
    pregunta = db.session.get(Pregunta, pregunta_id)
    if not pregunta:
        abort(404)
    if pregunta.autor_email != autor.email:
        abort(403)

    payload, error, form_data, selected_tag_ids = _validar_y_parsear_payload(
        request.form
    )
    if error:
        return _render_formulario(
            error=error,
            form_data=form_data,
            selected_tag_ids=selected_tag_ids,
            pregunta=pregunta,
        )

    pregunta.titulo = payload["titulo"]
    pregunta.cuerpo = payload["cuerpo"]
    pregunta.categoria_id = payload["categoria_id"]
    pregunta.modo_respuesta = payload["modo_respuesta"]
    pregunta.etiquetas = payload["etiquetas"]
    pregunta.fecha_actualizacion = datetime.now(UTC)
    pregunta.pendiente_respuesta_ia = pregunta.debe_activar_agente_ia()

    db.session.commit()

    return redirect(url_for("questions.detalle_pregunta", pregunta_id=pregunta.id))


@bp.post("/preguntas/<int:pregunta_id>/eliminar")
@login_requerido
def eliminar_pregunta(pregunta_id: int):
    autor = _usuario_actual()
    pregunta = db.session.get(Pregunta, pregunta_id)
    if not pregunta:
        abort(404)
    if pregunta.autor_email != autor.email:
        abort(403)

    db.session.delete(pregunta)
    db.session.commit()

    return redirect(url_for("questions.listar_preguntas"))


@bp.post("/preguntas/<int:pregunta_id>/responder")
@login_requerido
def responder_pregunta(pregunta_id: int):
    autor = _usuario_actual()
    pregunta = db.session.get(Pregunta, pregunta_id)
    if not pregunta:
        abort(404)

    if pregunta.modo_respuesta == "ia":
        abort(403)

    cuerpo_html = request.form.get("cuerpo", "").strip()

    # TODO: Mostrar error si el cuerpo esta vacio

    respuesta = RespuestaHumano(
        id_pregunta=pregunta.id, cuerpo=cuerpo_html, email_autor=autor.email
    )
    db.session.add(respuesta)
    db.session.commit()

    return redirect(url_for("questions.detalle_pregunta", pregunta_id=pregunta.id))


@bp.post("/respuesta/<int:respuesta_id>/delete")
@login_requerido
def eliminar_respuesta(respuesta_id: int):
    autor = _usuario_actual()
    respuesta = db.session.get(RespuestaHumano, respuesta_id)

    if not respuesta:
        abort(404)

    if respuesta.email_autor != autor.email:
        abort(403)

    pregunta_id = respuesta.pregunta.id

    db.session.delete(respuesta)
    db.session.commit()

    return redirect(url_for("questions.detalle_pregunta", pregunta_id=pregunta_id))


@bp.post("/respuesta/<tipo>/<int:respuesta_id>/validar")
@login_requerido
def verificar_respuesta(tipo: str, respuesta_id: int):
    autor = _usuario_actual()
    tipos = {"humano": RespuestaHumano, "ia": RespuestaIA}
    if tipo not in tipos:
        abort(404)

    tipo_respuesta = tipos[tipo]
    respuesta = db.session.get(tipo_respuesta, respuesta_id)

    if not respuesta:
        abort(404)

    if respuesta.pregunta.autor_email != autor.email:
        abort(403)

    respuesta.aceptada = not respuesta.aceptada
    db.session.commit()

    return redirect(
        url_for("questions.detalle_pregunta", pregunta_id=respuesta.pregunta.id)
    )


def procesar_preguntas_vencidas_24h(preguntas):
    hubo_cambios = False
    for pregunta in preguntas:
        if (
            not pregunta.respuestas_humano
            and not pregunta.respuestas_ia
            and pregunta.supero_24h_sin_respuesta
        ):
            generar_respuesta_ia_si_corresponde(pregunta)
            hubo_cambios = True
    if hubo_cambios:
        db.session.commit()

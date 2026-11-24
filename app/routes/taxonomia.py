from flask import Blueprint, redirect, render_template, request, url_for

from ..extensions import db
from ..models.category import Categoria
from ..models.category import MAX_LENGTH as MAX_CAT_LEN
from ..models.tags import Etiqueta
from ..models.tags import MAX_LENGTH as MAX_TAG_LEN

bp = Blueprint("taxonomia", __name__)


def _render_pagina(error=None):
    categorias = Categoria.query.order_by(Categoria.nombre.asc()).all()
    etiquetas = Etiqueta.query.order_by(Etiqueta.nombre.asc()).all()
    return render_template(
        "category_tags.html",
        categorias=categorias,
        etiquetas=etiquetas,
        error=error,
    )


@bp.get("/taxonomia")
def index():
    return _render_pagina()


@bp.post("/categorias")
def crear_categoria():
    nombre = request.form.get("nombre", "").strip()

    if not nombre:
        return _render_pagina(error="El nombre de la categoría es obligatorio")

    if len(nombre) > MAX_CAT_LEN:
        return _render_pagina(
            error=f"La categoría no debe superar los {MAX_CAT_LEN} caracteres"
        )

    if Categoria.query.filter(Categoria.nombre.ilike(nombre)).first():
        return _render_pagina(error="Esa categoría ya existe")

    db.session.add(Categoria(nombre=nombre))
    db.session.commit()
    return redirect(url_for("taxonomia.index"))


@bp.post("/etiquetas")
def crear_etiqueta():
    nombre = request.form.get("nombre", "").strip().lower()

    if not nombre:
        return _render_pagina(error="El nombre de la etiqueta es obligatorio")

    if len(nombre) > MAX_TAG_LEN:
        return _render_pagina(
            error=f"La etiqueta no debe superar los {MAX_TAG_LEN} caracteres"
        )

    if Etiqueta.query.filter(Etiqueta.nombre.ilike(nombre)).first():
        return _render_pagina(error="Esa etiqueta ya existe")

    db.session.add(Etiqueta(nombre=nombre))
    db.session.commit()
    return redirect(url_for("taxonomia.index"))

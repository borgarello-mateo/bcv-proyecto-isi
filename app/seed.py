from .extensions import db
from .models.category import Categoria
from .models.tags import Etiqueta

CATEGORIAS_INICIALES = ["Python", "Flask", "Base de datos"]
ETIQUETAS_INICIALES = ["ia-help", "bug-report", "code-review", "database"]


def seed_defaults():
    for nombre in CATEGORIAS_INICIALES:
        if not Categoria.query.filter_by(nombre=nombre).first():
            db.session.add(Categoria(nombre=nombre))

    for nombre in ETIQUETAS_INICIALES:
        if not Etiqueta.query.filter_by(nombre=nombre).first():
            db.session.add(Etiqueta(nombre=nombre))

    db.session.commit()

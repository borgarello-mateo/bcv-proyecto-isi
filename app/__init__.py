import os

from flask import Flask

from config import config

from .extensions import db, migrate


def create_app(environment="development"):
    app = Flask(__name__, instance_relative_config=True)

    os.makedirs(app.instance_path, exist_ok=True)

    app.config.from_object(config[environment])

    # Inicilaizar extensiones
    db.init_app(app)
    migrate.init_app(app, db)

    #Importar modelos
    from .models import category, tags, user
    from .seed import seed_defaults

    # Registrar bp de usuarios (ruta I)
    from .routes.auth import bp as auth_bp
    from .routes.users import bp as users_bp
    from .routes.taxonomia import bp as taxonomia_bp

    app.register_blueprint(users_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(taxonomia_bp)

    # TODO: reemplazar con un valor secreto
    app.secret_key = "valor-no-secreto"

    with app.app_context():
        db.create_all()
        seed_defaults()

    return app

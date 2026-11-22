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

    # Registrar bp de usuarios (ruta I)
    from .routes.users import bp as users_bp

    app.register_blueprint(users_bp)

    return app

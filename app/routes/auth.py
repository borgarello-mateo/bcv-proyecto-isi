from flask import Blueprint, redirect, render_template, request, session, url_for

from ..extensions import db
from ..models.user import User

bp = Blueprint("auth", __name__)

@bp.get("/register")
def index_register():
    return render_template("register.html")


@bp.get("/login")
def index_login():
    return render_template("login.html")


@bp.post("/register")
def register():
    email = request.form["email"].strip()
    password = request.form["password"]
    user = db.session.get(entity=User, ident=email) 

    if user:
        return render_template("register.html", error="Email ya usado")

    # TODO: Seguridad de contraseña
    user = User(email=email, password=password)
    db.session.add(user)
    db.session.commit()

    return redirect(url_for("auth.index_login"))


@bp.post("/login")
def login():
    email = request.form["email"]
    password = request.form["password"]
    user = db.session.get(entity=User, ident=email)

    if user == None:
        return render_template("login.html", error="Usuario no existente")

    # TODO: Seguridad de contraseña
    if user.password != password:
        return render_template("login.html", error="Contraseña incorrecta")

    session["user"] = email
    return redirect(url_for("users.index"))

from flask import Blueprint, redirect, render_template, request, session, url_for

bp = Blueprint("auth", __name__)

# TODO: Conectar a sql alchemy en vez de usar en memoria
usuarios = {}


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

    # TODO: una vez usando sql alchemy, cambiar lógica
    if email in usuarios:
        return render_template("register.html", error="Email ya usado")

    usuarios[email] = password

    return redirect(url_for("auth.index_login"))


@bp.post("/login")
def login():
    email = request.form["email"]
    password = request.form["password"]

    if email not in usuarios:
        return render_template("login.html", error="Usuario no existente")

    if usuarios[email] != password:
        return render_template("login.html", error="Contraseña incorrecta")

    session["user"] = email
    return redirect(url_for("users.index"))

from flask import Blueprint, render_template, session, redirect, url_for

bp = Blueprint("users", __name__)


@bp.route("/")
def index():
    user = None
    if "user" in session:
        user = session["user"]

    return render_template("dashboard.html", user=user)


@bp.post("/logout")
def logout():
    session["user"] = None
    return render_template("dashboard.html", user=None)

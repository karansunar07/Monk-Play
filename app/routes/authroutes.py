from flask import Blueprint, render_template

from app.controllers.authcontroller import login_user, register_user


auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/")
def home():
    return render_template("home.html")


@auth_bp.route("/login")
def login():
    return login_user()


@auth_bp.route("/register")
def register():
    return register_user()

from flask import Blueprint, request

from app.auth import login_required
from app.controllers import authController as authcontroller


auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/")
@login_required
def home():
    return authcontroller.home_page()


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        return authcontroller.login_user_post()
    return authcontroller.login_page()


@auth_bp.route("/register")
def register_page():
    return authcontroller.register_page()


@auth_bp.route("/cookies", methods=["GET", "POST"], endpoint="cookie_tools_route")
def cookies():
    return authcontroller.cookie_tools()


def register():
    return auth_bp

from flask import Blueprint

from app.controllers import authcontroller


auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/")
def home():
    return authcontroller.home_page()


@auth_bp.route("/login")
def login():
    return authcontroller.login_page()


@auth_bp.route("/register")
def register():
    return authcontroller.register_page()


@auth_bp.route("/cookies", methods=["GET", "POST"], endpoint="cookie_tools_route")
def cookies():
    return authcontroller.cookie_tools()

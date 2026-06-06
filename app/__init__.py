import secrets

from flask import Flask, abort, request, session

from app.controllers.authcontroller import cookie_tools
from app.routes.authroutes import auth_bp


def create_app():
    app = Flask(__name__)
    app.config["SECRET_KEY"] = "change-this-secret-key"

    @app.context_processor
    def inject_csrf_token():
        return {"csrf_token": get_csrf_token}

    @app.before_request
    def verify_csrf_token():
        if request.method == "POST":
            sent_token = request.form.get("csrf_token", "")
            session_token = session.get("csrf_token", "")
            if not sent_token or not session_token or not secrets.compare_digest(sent_token, session_token):
                abort(400, description="Invalid CSRF token.")

    app.add_url_rule("/cookies", endpoint="cookie_tools", view_func=cookie_tools, methods=["GET", "POST"])
    app.register_blueprint(auth_bp)

    return app


def get_csrf_token():
    token = session.get("csrf_token")
    if not token:
        token = secrets.token_urlsafe(32)
        session["csrf_token"] = token
    return token

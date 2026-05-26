from flask import Flask

from app.routes.authroutes import auth_bp


def create_app():
    app = Flask(__name__)
    app.config["SECRET_KEY"] = "change-this-secret-key"

    app.register_blueprint(auth_bp)

    return app

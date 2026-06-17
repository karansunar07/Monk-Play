from functools import wraps

import pytest
from flask import Blueprint, Flask, redirect, session, url_for


def login_required(view_func):
    @wraps(view_func)
    def wrapped_view(*args, **kwargs):
        if not session.get("user_id"):
            return redirect(url_for("auth.login"))
        return view_func(*args, **kwargs)

    return wrapped_view


@pytest.fixture
def client():
    app = Flask(__name__)
    app.secret_key = "secret_key"
    auth = Blueprint("auth", __name__)

    @auth.route("/login")
    def login():
        return "this is the login page"

    @auth.route("/home")
    @login_required
    def home():
        return "welcome home page"

    app.register_blueprint(auth)

    with app.test_client() as test_client:
        yield test_client


def test_locked_page_redirects_a_guest(client):
    response = client.get("/home")

    assert response.status_code == 302
    assert "/login" in response.headers["Location"]


def test_login_page_is_public(client):
    response = client.get("/login")

    assert response.status_code == 200
    assert b"this is the login page" in response.data


def test_locked_page_allows_authenticated_user(client):
    with client.session_transaction() as user_session:
        user_session["user_id"] = 1

    response = client.get("/home")

    assert response.status_code == 200
    assert b"welcome home page" in response.data

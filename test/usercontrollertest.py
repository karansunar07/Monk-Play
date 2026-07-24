import os
import pytest
from unittest.mock import patch, MagicMock
from werkzeug.security import generate_password_hash
from flask import Flask

from app.routes import authRoutes
PROJECT_ROOT = os.path.dirname(os.path.dirname(__file__))
TEMPLATE_DIR = os.path.join(PROJECT_ROOT, "app", "templates")
STATIC_DIR = os.path.join(PROJECT_ROOT, "app", "static")


@pytest.fixture(scope="module")
def app():
    app = Flask(
        __name__,
        template_folder=TEMPLATE_DIR,
        static_folder=STATIC_DIR,
    )
    app.secret_key = "test-secret"
    app.config["TESTING"] = True

    # register() mutates the module-level blueprint, so call it exactly once.
    app.register_blueprint(authRoutes.register())
    return app


@pytest.fixture
def client(app):
    with app.test_client() as client:
        yield client


def _login(client, role="user"):
    """Put a user in the session and stub the decorator's lookup."""
    with client.session_transaction() as sess:
        sess["user_id"] = 1
        sess["csrf_token"] = "test-csrf-token"
    patcher = patch(
        "app.auth.get_user_by_id",
        return_value={"id": 1, "role": role},
    )
    return patcher




def test_home_page(client):
    # "/" is protected by login_required, so a logged-in user is required.
    with _login(client, role="user"):
        response = client.get("/")
    assert response.status_code == 200


def test_home_page_redirects_guest(client):
    response = client.get("/")
    assert response.status_code == 302
    assert "/login" in response.location



def test_login_page_get(client):
    response = client.get("/login")
    assert response.status_code == 200


@patch("app.controllers.authController.get_connection")
def test_login_success(mock_conn, client):
    with client.session_transaction() as sess:
        sess["csrf_token"] = "test-csrf-token"

    fake_user = {
        "id": 1,
        "name": "Abishek",
        "email": "test@test.com",
        "password": generate_password_hash("password"),
        "role": "user",
    }

    cursor = MagicMock()
    cursor.fetchone.return_value = fake_user

    conn = MagicMock()
    conn.cursor.return_value = cursor

    mock_conn.return_value = conn

    response = client.post(
        "/login",
        data={
            "csrf_token": "test-csrf-token",
            "email": "test@test.com",
            "password": "password",
        },
        follow_redirects=False,
    )

    assert response.status_code == 302

    with client.session_transaction() as sess:
        assert sess["user_id"] == 1


@patch("app.controllers.authController.get_connection")
def test_login_invalid(mock_conn, client):
    with client.session_transaction() as sess:
        sess["csrf_token"] = "test-csrf-token"

    cursor = MagicMock()
    cursor.fetchone.return_value = None

    conn = MagicMock()
    conn.cursor.return_value = cursor

    mock_conn.return_value = conn

    response = client.post(
        "/login",
        data={
            "csrf_token": "test-csrf-token",
            "email": "wrong@test.com",
            "password": "wrong",
        },
    )

    assert response.status_code == 200

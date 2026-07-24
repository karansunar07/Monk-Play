from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from werkzeug.security import generate_password_hash


PROJECT_ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="module")
def app_module():
    app_path = PROJECT_ROOT / "app.py"
    spec = spec_from_file_location("monk_play_app_under_test", app_path)
    module = module_from_spec(spec)

    with patch("app.database.create_tables"):
        spec.loader.exec_module(module)

    module.app.config.update(TESTING=True, WTF_CSRF_ENABLED=False)
    return module


@pytest.fixture
def client(app_module):
    app_module.app.config["SECRET_KEY"] = "test-secret"
    with app_module.app.test_client() as test_client:
        yield test_client


def _csrf_session(client, user_id=None, role="user", name="Test User"):
    with client.session_transaction() as sess:
        sess["csrf_token"] = "test-csrf-token"
        if user_id:
            sess["user_id"] = user_id
            sess["user_name"] = name
            sess["user_role"] = role


def _mock_connection(fetchone_values=None, fetchall_values=None):
    cursor = MagicMock()
    cursor.fetchone.side_effect = fetchone_values or []
    cursor.fetchall.side_effect = fetchall_values or []

    conn = MagicMock()
    conn.cursor.return_value = cursor
    return conn, cursor


def test_home_page_loads_without_database(app_module, client):
    with patch.object(app_module, "get_connection", return_value=None):
        response = client.get("/")

    assert response.status_code == 200
    assert b"Monk Play" in response.data


def test_songs_search_loads_full_library_for_browser_filtering(app_module, client):
    conn, cursor = _mock_connection(fetchall_values=[[]])

    with patch.object(app_module, "get_connection", return_value=conn):
        response = client.get("/songs?q=moon")

    assert response.status_code == 200
    executed_query, params = cursor.execute.call_args.args
    assert "LIKE" not in executed_query
    assert params == []


def test_profile_redirects_guest_to_login(client):
    response = client.get("/profile")

    assert response.status_code == 302
    assert "/login" in response.location


def test_login_success_sets_session(app_module, client):
    _csrf_session(client)
    fake_user = {
        "id": 7,
        "name": "Karan",
        "email": "karan@example.com",
        "password": generate_password_hash("secret123"),
        "role": "artist",
        "avatar_url": "/static/uploads/profiles/test.png",
    }
    conn, _cursor = _mock_connection(fetchone_values=[fake_user])

    with patch.object(app_module, "get_connection", return_value=conn):
        response = client.post(
            "/login",
            data={"csrf_token": "test-csrf-token", "email": fake_user["email"], "password": "secret123"},
            follow_redirects=False,
        )

    assert response.status_code == 302
    executed_queries = [call.args[0] for call in _cursor.execute.call_args_list]
    assert any("INSERT INTO login_events" in query for query in executed_queries)
    with client.session_transaction() as sess:
        assert sess["user_id"] == 7
        assert sess["user_role"] == "artist"
        assert sess["avatar_url"] == "/static/uploads/profiles/test.png"


def test_change_password_updates_hash(app_module, client):
    _csrf_session(client, user_id=3)
    fake_user = {"id": 3, "password": generate_password_hash("oldpass")}
    conn, cursor = _mock_connection(fetchone_values=[fake_user])

    with patch.object(app_module, "get_connection", return_value=conn):
        response = client.post(
            "/profile/password",
            data={
                "csrf_token": "test-csrf-token",
                "current_password": "oldpass",
                "new_password": "newpass1",
                "confirm_password": "newpass1",
            },
            follow_redirects=False,
        )

    assert response.status_code == 302
    update_call = cursor.execute.call_args_list[-1].args
    assert "UPDATE users SET password" in update_call[0]
    assert update_call[1][1] == 3
    assert update_call[1][0] != "newpass1"


def test_profile_avatar_rejects_invalid_file(app_module, client):
    _csrf_session(client, user_id=3)

    with patch.object(app_module, "get_connection") as mock_get_connection:
        response = client.post(
            "/profile/avatar",
            data={"csrf_token": "test-csrf-token"},
            follow_redirects=False,
        )

    assert response.status_code == 302
    mock_get_connection.assert_not_called()

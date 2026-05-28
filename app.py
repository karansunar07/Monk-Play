import os
import secrets
from collections import deque
from datetime import datetime
from urllib.parse import urlencode

import requests
from flask import Flask, flash, has_request_context, redirect, render_template, request, session, url_for
from werkzeug.exceptions import HTTPException
from werkzeug.security import check_password_hash, generate_password_hash

import config
from app.database import create_tables, get_connection

BASE_DIR = os.path.dirname(__file__)
TEMPLATE_DIR = os.path.join(BASE_DIR, "app", "templates")
STATIC_DIR = os.path.join(BASE_DIR, "app", "statics")


app = Flask(__name__, template_folder=TEMPLATE_DIR, static_folder=STATIC_DIR)
app.config["SECRET_KEY"] = config.SECRET_KEY

SPOTIFY_SCOPES = "playlist-read-private playlist-read-collaborative user-read-private"
APP_LOGS = deque(maxlen=120)


@app.context_processor
def inject_provider_state():
    return {
        "spotify_connected": bool(session.get("spotify_access_token")),
        "is_admin": session.get("user_role") == "admin",
    }


def write_app_log(level, message, details=""):
    path = request.path if has_request_context() else ""
    method = request.method if has_request_context() else ""
    APP_LOGS.appendleft(
        {
            "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "level": level,
            "message": message,
            "details": details,
            "path": path,
            "method": method,
        }
    )


@app.before_request
def log_request_start():
    if request.endpoint != "static":
        write_app_log("info", "Request started")


@app.after_request
def log_request_finish(response):
    if request.endpoint != "static":
        level = "error" if response.status_code >= 500 else "warning" if response.status_code >= 400 else "info"
        write_app_log(level, f"Request finished with {response.status_code}")
    return response


@app.errorhandler(Exception)
def log_unhandled_error(error):
    if isinstance(error, HTTPException):
        write_app_log("warning", f"HTTP error {error.code}", error.description)
        return error

    write_app_log("error", "Unhandled application error", str(error))
    flash("Something went wrong. Check the admin logs for details.", "danger")
    return redirect(url_for("dashboard" if session.get("user_id") else "login"))


def login_user_session(user):
    session["user_id"] = user["id"]
    session["user_name"] = user["name"]
    session["user_role"] = user.get("role", "user")


def get_role_for_new_user(cursor):
    cursor.execute("SELECT COUNT(*) AS total FROM users")
    result = cursor.fetchone() or {}
    return "admin" if (result.get("total") or 0) == 0 else "user"


def get_imported_playlists(user_id):
    if not user_id:
        return []

    conn = get_connection()
    if conn is None:
        return []

    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT id, spotify_playlist_id, name, owner_name, image_url, spotify_url, track_count
        FROM imported_playlists
        WHERE user_id = %s
        ORDER BY id DESC
        """,
        (user_id,),
    )
    playlists = cursor.fetchall()
    cursor.close()
    conn.close()
    return playlists


def is_admin_user():
    return session.get("user_role") == "admin"


def get_admin_users():
    conn = get_connection()
    if conn is None:
        return []

    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT users.id, users.name, users.email, users.role,
            COUNT(imported_playlists.id) AS playlist_count
        FROM users
        LEFT JOIN imported_playlists ON imported_playlists.user_id = users.id
        GROUP BY users.id, users.name, users.email, users.role
        ORDER BY users.id DESC
        """
    )
    users = cursor.fetchall()
    cursor.close()
    conn.close()
    return users


def get_dashboard_data(user_id, user_role):
    dashboard = {
        "playlist_count": 0,
        "track_count": 0,
        "recent_playlists": [],
        "user_count": 0,
        "admin_count": 0,
        "spotify_connected": bool(session.get("spotify_access_token")),
    }

    if not user_id:
        return dashboard

    conn = get_connection()
    if conn is None:
        return dashboard

    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT COUNT(*) AS playlist_count, COALESCE(SUM(track_count), 0) AS track_count
        FROM imported_playlists
        WHERE user_id = %s
        """,
        (user_id,),
    )
    personal_totals = cursor.fetchone() or {}
    dashboard["playlist_count"] = personal_totals.get("playlist_count", 0)
    dashboard["track_count"] = personal_totals.get("track_count", 0)

    cursor.execute(
        """
        SELECT name, owner_name, track_count, spotify_url
        FROM imported_playlists
        WHERE user_id = %s
        ORDER BY id DESC
        LIMIT 4
        """,
        (user_id,),
    )
    dashboard["recent_playlists"] = cursor.fetchall()

    if user_role == "admin":
        cursor.execute(
            """
            SELECT
                COUNT(*) AS user_count,
                SUM(CASE WHEN role = 'admin' THEN 1 ELSE 0 END) AS admin_count
            FROM users
            """
        )
        admin_totals = cursor.fetchone() or {}
        dashboard["user_count"] = admin_totals.get("user_count", 0)
        dashboard["admin_count"] = admin_totals.get("admin_count", 0)

    cursor.close()
    conn.close()
    return dashboard


def add_manual_track(imported_playlist_id, user_id, track_data, is_admin=False):
    conn = get_connection()
    if conn is None:
        return False, "Database is not available right now."

    cursor = conn.cursor()
    if is_admin:
        cursor.execute(
            """
            SELECT id FROM imported_playlists
            WHERE id = %s
            """,
            (imported_playlist_id,),
        )
    else:
        cursor.execute(
            """
            SELECT id FROM imported_playlists
            WHERE id = %s AND user_id = %s
            """,
            (imported_playlist_id, user_id),
        )

    playlist = cursor.fetchone()
    if not playlist:
        cursor.close()
        conn.close()
        return False, "That playlist could not be found."

    cursor.execute(
        """
        SELECT COALESCE(MAX(track_position), 0) AS last_position
        FROM imported_playlist_tracks
        WHERE imported_playlist_id = %s
        """,
        (imported_playlist_id,),
    )
    position_result = cursor.fetchone() or {}
    next_position = (position_result.get("last_position") or 0) + 1

    cursor.execute(
        """
        INSERT INTO imported_playlist_tracks (
            imported_playlist_id, spotify_track_id, track_name, artist_names,
            album_name, spotify_url, duration_ms, track_position
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """,
        (
            imported_playlist_id,
            "",
            track_data["track_name"],
            track_data["artist_names"],
            track_data["album_name"],
            track_data["spotify_url"],
            track_data["duration_ms"],
            next_position,
        ),
    )
    cursor.execute(
        """
        UPDATE imported_playlists
        SET track_count = track_count + 1
        WHERE id = %s
        """,
        (imported_playlist_id,),
    )
    conn.commit()
    cursor.close()
    conn.close()
    return True, None


def spotify_api_get(endpoint, token, params=None):
    response = requests.get(
        f"https://api.spotify.com/v1/{endpoint}",
        headers={"Authorization": f"Bearer {token}"},
        params=params,
        timeout=20,
    )
    return response


def refresh_spotify_access_token():
    refresh_token = session.get("spotify_refresh_token")
    if not refresh_token or not config.SPOTIFY_CLIENT_ID or not config.SPOTIFY_CLIENT_SECRET:
        return None

    response = requests.post(
        "https://accounts.spotify.com/api/token",
        data={
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
            "client_id": config.SPOTIFY_CLIENT_ID,
            "client_secret": config.SPOTIFY_CLIENT_SECRET,
        },
        timeout=20,
    )
    if response.status_code != 200:
        return None

    token_data = response.json()
    access_token = token_data.get("access_token")
    if not access_token:
        return None

    session["spotify_access_token"] = access_token
    if token_data.get("refresh_token"):
        session["spotify_refresh_token"] = token_data["refresh_token"]
    return access_token


def spotify_get_with_refresh(endpoint, params=None):
    access_token = session.get("spotify_access_token")
    if not access_token:
        return None

    response = spotify_api_get(endpoint, access_token, params=params)
    if response.status_code != 401:
        return response

    refreshed_access_token = refresh_spotify_access_token()
    if not refreshed_access_token:
        return response

    return spotify_api_get(endpoint, refreshed_access_token, params=params)


def get_spotify_playlists():
    response = spotify_get_with_refresh("me/playlists", params={"limit": 20})
    if response is None or response.status_code != 200:
        return []

    payload = response.json()
    playlists = payload.get("items", [])

    profile_response = spotify_get_with_refresh("me")
    current_user_id = ""
    if profile_response is not None and profile_response.status_code == 200:
        current_user_id = profile_response.json().get("id", "")

    for playlist in playlists:
        owner_id = (playlist.get("owner") or {}).get("id", "")
        playlist["can_import_tracks"] = bool(
            current_user_id and (owner_id == current_user_id or playlist.get("collaborative"))
        )

    return playlists


def fetch_playlist_tracks(playlist_id, token):
    tracks = []
    next_url = f"https://api.spotify.com/v1/playlists/{playlist_id}/items?limit=50"

    while next_url:
        response = requests.get(
            next_url,
            headers={"Authorization": f"Bearer {token}"},
            timeout=20,
        )
        if response.status_code == 401:
            refreshed_access_token = refresh_spotify_access_token()
            if not refreshed_access_token:
                return None, "Your Spotify session expired. Reconnect Spotify and try again."

            token = refreshed_access_token
            response = requests.get(
                next_url,
                headers={"Authorization": f"Bearer {token}"},
                timeout=20,
            )

        if response.status_code != 200:
            error_payload = {}
            try:
                error_payload = response.json()
            except ValueError:
                error_payload = {}

            error_message = (error_payload.get("error") or {}).get("message")
            if response.status_code == 403:
                return None, (
                    "Spotify only allows this app to import tracks from playlists you own "
                    "or playlists where you are a collaborator. Create your own copy of "
                    "that playlist in Spotify, reconnect Spotify, then import the copy."
                )
            if response.status_code == 404:
                return None, "Spotify could not find that playlist or its tracks."
            if error_message:
                return None, f"Spotify could not fetch the playlist tracks: {error_message}"
            return None, "Spotify could not fetch the playlist tracks right now."

        payload = response.json()
        for item in payload.get("items", []):
            track = item.get("track") or item.get("item")
            if not track or track.get("type") != "track":
                continue

            artists = ", ".join(artist["name"] for artist in track.get("artists", []))
            album = (track.get("album") or {}).get("name", "")
            tracks.append(
                {
                    "spotify_track_id": track.get("id", ""),
                    "name": track.get("name", ""),
                    "artists": artists,
                    "album": album,
                    "spotify_url": (track.get("external_urls") or {}).get("spotify", ""),
                    "duration_ms": track.get("duration_ms", 0),
                }
            )

        next_url = payload.get("next")

    return tracks, None


def save_imported_playlist(user_id, playlist_data, tracks):
    conn = get_connection()
    if conn is None:
        return False

    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT id FROM imported_playlists
        WHERE user_id = %s AND spotify_playlist_id = %s
        """,
        (user_id, playlist_data["spotify_playlist_id"]),
    )
    existing = cursor.fetchone()

    if existing:
        playlist_row_id = existing["id"]
        cursor.execute(
            """
            UPDATE imported_playlists
            SET name = %s, description = %s, owner_name = %s, image_url = %s,
                spotify_url = %s, track_count = %s
            WHERE id = %s
            """,
            (
                playlist_data["name"],
                playlist_data["description"],
                playlist_data["owner_name"],
                playlist_data["image_url"],
                playlist_data["spotify_url"],
                playlist_data["track_count"],
                playlist_row_id,
            ),
        )
        cursor.execute(
            "DELETE FROM imported_playlist_tracks WHERE imported_playlist_id = %s",
            (playlist_row_id,),
        )
    else:
        cursor.execute(
            """
            INSERT INTO imported_playlists (
                user_id, spotify_playlist_id, name, description, owner_name,
                image_url, spotify_url, track_count
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                user_id,
                playlist_data["spotify_playlist_id"],
                playlist_data["name"],
                playlist_data["description"],
                playlist_data["owner_name"],
                playlist_data["image_url"],
                playlist_data["spotify_url"],
                playlist_data["track_count"],
            ),
        )
        playlist_row_id = cursor.lastrowid

    for position, track in enumerate(tracks, start=1):
        cursor.execute(
            """
            INSERT INTO imported_playlist_tracks (
                imported_playlist_id, spotify_track_id, track_name, artist_names,
                album_name, spotify_url, duration_ms, track_position
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                playlist_row_id,
                track["spotify_track_id"],
                track["name"],
                track["artists"],
                track["album"],
                track["spotify_url"],
                track["duration_ms"],
                position,
            ),
        )

    conn.commit()
    cursor.close()
    conn.close()
    return True


@app.route("/")
def home():
    imported_playlists = get_imported_playlists(session.get("user_id"))
    return render_template(
        "home.html",
        user_name=session.get("user_name"),
        imported_playlists=imported_playlists,
    )


@app.route("/dashboard")
def dashboard():
    if not session.get("user_id"):
        flash("Login first to open your dashboard.", "danger")
        return redirect(url_for("login"))

    dashboard_data = get_dashboard_data(session.get("user_id"), session.get("user_role"))
    return render_template(
        "dashboard.html",
        user_name=session.get("user_name"),
        user_role=session.get("user_role", "user"),
        dashboard_data=dashboard_data,
        admin_users=get_admin_users() if is_admin_user() else [],
        app_logs=list(APP_LOGS) if is_admin_user() else [],
    )


@app.route("/admin/users/<int:user_id>/role", methods=["POST"])
def update_user_role(user_id):
    if not session.get("user_id"):
        flash("Login first to manage users.", "danger")
        return redirect(url_for("login"))

    if not is_admin_user():
        flash("Only admins can change user roles.", "danger")
        return redirect(url_for("dashboard"))

    new_role = request.form.get("role", "").strip().lower()
    if new_role not in {"admin", "user"}:
        flash("Choose a valid role.", "danger")
        return redirect(url_for("dashboard"))

    conn = get_connection()
    if conn is None:
        flash("Database is not available right now.", "danger")
        return redirect(url_for("dashboard"))

    cursor = conn.cursor()
    cursor.execute("SELECT id, role FROM users WHERE id = %s", (user_id,))
    user = cursor.fetchone()
    if not user:
        cursor.close()
        conn.close()
        flash("That user could not be found.", "danger")
        return redirect(url_for("dashboard"))

    if user_id == session.get("user_id") and user.get("role") == "admin" and new_role == "user":
        cursor.execute("SELECT COUNT(*) AS admin_count FROM users WHERE role = 'admin'")
        admin_count = (cursor.fetchone() or {}).get("admin_count", 0)
        if admin_count <= 1:
            cursor.close()
            conn.close()
            flash("You cannot remove the last admin account.", "danger")
            return redirect(url_for("dashboard"))

    cursor.execute("UPDATE users SET role = %s WHERE id = %s", (new_role, user_id))
    conn.commit()
    cursor.close()
    conn.close()

    if user_id == session.get("user_id"):
        session["user_role"] = new_role

    flash("User role updated.", "success")
    return redirect(url_for("dashboard"))


@app.route("/admin/manual-track", methods=["POST"])
def add_manual_track_route():
    if not session.get("user_id"):
        flash("Login first to manage playlists.", "danger")
        return redirect(url_for("login"))

    if session.get("user_role") != "admin":
        flash("Only admin accounts can add songs manually.", "danger")
        return redirect(url_for("home"))

    playlist_id = request.form.get("imported_playlist_id", "").strip()
    track_name = request.form.get("track_name", "").strip()
    artist_names = request.form.get("artist_names", "").strip()
    album_name = request.form.get("album_name", "").strip()
    spotify_url = request.form.get("spotify_url", "").strip()
    duration_minutes = request.form.get("duration_minutes", "0").strip()
    duration_seconds = request.form.get("duration_seconds", "0").strip()

    if not playlist_id or not track_name or not artist_names:
        flash("Playlist, song name, and artist name are required.", "danger")
        return redirect(url_for("home"))

    try:
        imported_playlist_id = int(playlist_id)
        minutes = max(int(duration_minutes or 0), 0)
        seconds = max(int(duration_seconds or 0), 0)
    except ValueError:
        flash("Song duration must be numeric.", "danger")
        return redirect(url_for("home"))

    if seconds >= 60:
        flash("Seconds must be less than 60.", "danger")
        return redirect(url_for("home"))

    track_data = {
        "track_name": track_name,
        "artist_names": artist_names,
        "album_name": album_name,
        "spotify_url": spotify_url,
        "duration_ms": ((minutes * 60) + seconds) * 1000,
    }
    saved, error_message = add_manual_track(
        imported_playlist_id,
        session.get("user_id"),
        track_data,
        is_admin=True,
    )
    if not saved:
        flash(error_message or "The manual song could not be saved.", "danger")
        return redirect(url_for("home"))

    flash("Song added manually to the playlist.", "success")
    return redirect(url_for("home"))


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        if not email or not password:
            flash("Email and password are required.", "danger")
            return redirect(url_for("login"))

        conn = get_connection()
        if conn is None:
            flash("Database is not available right now.", "danger")
            return redirect(url_for("login"))

        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
        user = cursor.fetchone()
        cursor.close()
        conn.close()

        if user and check_password_hash(user["password"], password):
            login_user_session(user)
            flash("Login successful!", "success")
            return redirect(url_for("home"))

        flash("Invalid email or password.", "danger")
        return redirect(url_for("login"))

    return render_template("login.html")


@app.route("/spotify/connect")
def spotify_connect():
    if not session.get("user_id"):
        flash("Login first before connecting Spotify.", "danger")
        return redirect(url_for("login"))

    if not config.SPOTIFY_CLIENT_ID or not config.SPOTIFY_CLIENT_SECRET:
        flash("Add your Spotify client ID and secret in config.py first.", "danger")
        return redirect(url_for("spotify_import"))

    query = urlencode(
        {
            "client_id": config.SPOTIFY_CLIENT_ID,
            "response_type": "code",
            "redirect_uri": config.SPOTIFY_REDIRECT_URI,
            "scope": SPOTIFY_SCOPES,
            "show_dialog": "true",
        }
    )
    return redirect(f"https://accounts.spotify.com/authorize?{query}")


@app.route("/spotify/callback")
def spotify_callback():
    code = request.args.get("code")
    error = request.args.get("error")

    if error:
        flash(f"Spotify authorization failed: {error}", "danger")
        return redirect(url_for("spotify_import"))

    if not code:
        flash("Spotify did not return an authorization code.", "danger")
        return redirect(url_for("spotify_import"))

    response = requests.post(
        "https://accounts.spotify.com/api/token",
        data={
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": config.SPOTIFY_REDIRECT_URI,
            "client_id": config.SPOTIFY_CLIENT_ID,
            "client_secret": config.SPOTIFY_CLIENT_SECRET,
        },
        timeout=20,
    )

    if response.status_code != 200:
        flash("Could not connect to Spotify. Check your client keys and redirect URI.", "danger")
        return redirect(url_for("spotify_import"))

    token_data = response.json()
    session["spotify_access_token"] = token_data.get("access_token")
    session["spotify_refresh_token"] = token_data.get("refresh_token", "")
    flash("Spotify connected successfully.", "success")
    return redirect(url_for("spotify_import"))


@app.route("/spotify/disconnect")
def spotify_disconnect():
    session.pop("spotify_access_token", None)
    session.pop("spotify_refresh_token", None)
    flash("Spotify disconnected.", "success")
    return redirect(url_for("spotify_import"))


@app.route("/spotify/import", methods=["GET", "POST"])
def spotify_import():
    if not session.get("user_id"):
        flash("Login first to import playlists from Spotify.", "danger")
        return redirect(url_for("login"))

    spotify_playlists = []
    imported_tracks = []
    selected_playlist = None

    if session.get("spotify_access_token"):
        spotify_playlists = get_spotify_playlists()

    if request.method == "POST":
        playlist_id = request.form.get("playlist_id", "").strip()
        access_token = session.get("spotify_access_token")

        if not access_token:
            flash("Connect Spotify before importing a playlist.", "danger")
            return redirect(url_for("spotify_import"))

        if not playlist_id:
            flash("Choose a playlist to import.", "danger")
            return redirect(url_for("spotify_import"))

        playlist_response = spotify_get_with_refresh(f"playlists/{playlist_id}")
        if playlist_response is None:
            flash("Connect Spotify before importing a playlist.", "danger")
            return redirect(url_for("spotify_import"))

        if playlist_response.status_code != 200:
            if playlist_response.status_code == 401:
                flash("Your Spotify session expired. Reconnect Spotify and try again.", "danger")
            elif playlist_response.status_code == 403:
                flash("Spotify denied access to that playlist for the connected account.", "danger")
            elif playlist_response.status_code == 404:
                flash("Spotify could not find that playlist.", "danger")
            else:
                flash("That playlist could not be loaded from Spotify right now.", "danger")
            return redirect(url_for("spotify_import"))

        playlist_payload = playlist_response.json()
        tracks, track_error = fetch_playlist_tracks(playlist_id, session.get("spotify_access_token"))

        if tracks is None:
            flash(track_error or "The playlist tracks could not be fetched from Spotify.", "danger")
            return redirect(url_for("spotify_import"))

        selected_playlist = {
            "spotify_playlist_id": playlist_payload.get("id", ""),
            "name": playlist_payload.get("name", "Spotify Playlist"),
            "description": playlist_payload.get("description", ""),
            "owner_name": (playlist_payload.get("owner") or {}).get("display_name", "Spotify User"),
            "image_url": ((playlist_payload.get("images") or [{}])[0]).get("url", ""),
            "spotify_url": (playlist_payload.get("external_urls") or {}).get("spotify", ""),
            "track_count": len(tracks),
        }

        if save_imported_playlist(session.get("user_id"), selected_playlist, tracks):
            flash("Spotify playlist imported successfully.", "success")
            imported_tracks = tracks
        else:
            flash("The playlist could not be saved to your local database.", "danger")

    return render_template(
        "spotify_import.html",
        spotify_playlists=spotify_playlists,
        imported_tracks=imported_tracks,
        selected_playlist=selected_playlist,
    )


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        if not name or not email or not password:
            flash("All fields are required!", "danger")
            return redirect(url_for("register"))
        if len(name) > 100:
            flash("Name must be less than 100 characters!", "danger")
            return redirect(url_for("register"))
        if len(email) > 100:
            flash("Email must be less than 100 characters!", "danger")
            return redirect(url_for("register"))
        if len(password) < 6:
            flash("Password must be at least 6 characters!", "danger")
            return redirect(url_for("register"))

        conn = get_connection()
        if conn is None:
            flash("Database is not available right now.", "danger")
            return redirect(url_for("register"))

        cursor = conn.cursor()
        cursor.execute("SELECT id FROM users WHERE email = %s", (email,))
        if cursor.fetchone():
            cursor.close()
            conn.close()
            flash("Email already exists!", "danger")
            return redirect(url_for("register"))

        role = get_role_for_new_user(cursor)
        cursor.execute(
            "INSERT INTO users (name, email, password, role) VALUES (%s, %s, %s, %s)",
            (name, email, generate_password_hash(password), role),
        )
        conn.commit()
        cursor.close()
        conn.close()

        if role == "admin":
            flash("Registration successful. Your account has admin access.", "success")
        else:
            flash("Registration successful! Please login.", "success")
        return redirect(url_for("login"))

    return render_template("register.html")


@app.route("/logout")
def logout():
    session.clear()
    flash("Logged out successfully.", "success")
    return redirect(url_for("home"))


create_tables()





if __name__ == "__main__":
    app.run(debug=True)

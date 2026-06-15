from flask import flash, redirect, render_template, request, session, url_for


COOKIE_MAX_AGE = 60 * 60 * 24 * 30
COOKIE_FIELDS = {
    "monk_listener_name": "listener_name",
    "monk_music_preference": "music_preference",
}


def home_page():
    return render_template("home.html")


def login_page():
    return render_template("login.html")


def register_page():
    return render_template("register.html")


# Backward-compatible names for older package imports.
login_user = login_page
register_user = register_page


def is_admin_session():
    return session.get("user_role") == "admin"


def redirect_to_current_page():
    return redirect(url_for(request.endpoint))


def validate_cookie_form():
    listener_name = request.form.get("listener_name", "").strip()
    music_preference = request.form.get("music_preference", "").strip()

    if not listener_name or not music_preference:
        return None, None, "Listener name and music preference are required."
    if len(listener_name) > 80 or len(music_preference) > 80:
        return None, None, "Cookie values must be less than 80 characters."

    return listener_name, music_preference, None


def cookie_tools():
    if not session.get("user_id"):
        flash("Login first to open cookie tools.", "danger")
        return redirect(url_for("auth.login"))

    if not is_admin_session():
        flash("Only admins can open cookie tools.", "danger")
        return redirect(url_for("auth.home"))

    if request.method == "POST":
        action = request.form.get("action", "save")
        response = redirect_to_current_page()

        if action == "clear":
            for cookie_name in COOKIE_FIELDS:
                response.delete_cookie(cookie_name)
            flash("Saved cookies cleared from this browser.", "success")
            return response

        listener_name, music_preference, error_message = validate_cookie_form()
        if error_message:
            flash(error_message, "danger")
            return redirect_to_current_page()

        response.set_cookie(
            "monk_listener_name",
            listener_name,
            max_age=COOKIE_MAX_AGE,
            httponly=True,
            samesite="Lax",
        )
        response.set_cookie(
            "monk_music_preference",
            music_preference,
            max_age=COOKIE_MAX_AGE,
            httponly=True,
            samesite="Lax",
        )
        flash("Cookie values saved in this browser.", "success")
        return response

    return render_template(
        "cookies.html",
        listener_name=request.cookies.get("monk_listener_name", ""),
        music_preference=request.cookies.get("monk_music_preference", ""),
    )

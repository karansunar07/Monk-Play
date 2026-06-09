from flask import flash, redirect, render_template, request, session, url_for


COOKIE_MAX_AGE = 60 * 60 * 24 * 30


def login_user():
    return render_template("login.html")


def register_user():
    return render_template("register.html")


def cookie_tools():
    if not session.get("user_id"):
        flash("Login first to open cookie tools.", "danger")
        return redirect(url_for("auth.login"))

    if session.get("user_role") != "admin":
        flash("Only admins can open cookie tools.", "danger")
        return redirect(url_for("auth.home"))

    if request.method == "POST":
        action = request.form.get("action", "save")
        response = redirect(url_for(request.endpoint))

        if action == "clear":
            response.delete_cookie("monk_listener_name")
            response.delete_cookie("monk_music_preference")
            flash("Saved cookies cleared from this browser.", "success")
            return response

        listener_name = request.form.get("listener_name", "").strip()
        music_preference = request.form.get("music_preference", "").strip()

        if not listener_name or not music_preference:
            flash("Listener name and music preference are required.", "danger")
            return redirect(url_for(request.endpoint))
        if len(listener_name) > 80 or len(music_preference) > 80:
            flash("Cookie values must be less than 80 characters.", "danger")
            return redirect(url_for(request.endpoint))

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

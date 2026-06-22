from functools import wraps

from flask import redirect, session, url_for


def get_user_by_id(user_id):
    if not user_id:
        return None
    return {"id": 1, "role": "user"}  # Mock user object for testing purposes


def login_required(view_func):
    @wraps(view_func)
    def wrapped_view(*args, **kwargs):
        user = get_user_by_id(session.get("user_id"))
        if not user:
            return redirect(url_for("auth.login"))
        return view_func(*args, **kwargs)

    return wrapped_view

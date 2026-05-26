from flask import render_template


def login_user():
    return render_template("login.html")


def register_user():
    return render_template("register.html")

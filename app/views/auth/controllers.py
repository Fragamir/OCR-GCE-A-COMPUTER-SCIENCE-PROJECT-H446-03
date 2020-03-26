from flask import Blueprint, render_template, url_for, redirect, flash, request
from flask_login import current_user, login_user, logout_user, login_required
from app.models import User
from app.forms import LoginForm, RegisterForm
from werkzeug.urls import url_parse
from functools import wraps

auth = Blueprint("auth", __name__, template_folder="templates", static_folder="static")


def logout_required(route=None):
    def decorator(func):
        @wraps(func)
        def decorated_view(*args, **kwargs):
            if not current_user.is_authenticated:
                return func(*args, **kwargs)
            else:
                if route:
                    return redirect(url_for("auth.logout", next=route))
                else:
                    return redirect(url_for("auth.logout"))
        return decorated_view
    return decorator


@auth.route("/login", methods=["GET", "POST"])
@logout_required("auth.login")
def login():
    next_page = request.args.get("next")
    form = LoginForm()
    if form.validate_on_submit():
        username = request.form["username"]
        user = User.query().filter(User.username == username).first()
        login_user(user)
        if not next_page or url_parse(next_page).netloc != "":
            return redirect(url_for("dashboard.reroute"))
        return redirect(next_page)
    return render_template("auth/login.html", form=form, title="Login",
                           page="sign_in", next=next_page, user=current_user)


@auth.route("/logout")
@login_required
def logout():
    next_page = request.args.get("next", None)
    logout = request.args.get("logout", False)
    if not next_page or logout:
        logout_user()
        flash("Logged out")
        if logout and next_page:
            return redirect(url_for(next_page))
        return redirect("/")
    return render_template("auth/logout.html", user=current_user,
                           next=next_page)


@auth.route("/register", methods=["GET", "POST"])
@logout_required("auth.register")
def register():
    next_page = request.args.get("next")
    form = RegisterForm()
    if form.validate_on_submit():
        username = request.form["username"]
        email = request.form["email"].lower()
        password = request.form["password"]
        first_name = request.form["first_name"]
        pref_name = request.form.get("pref_name", "")
        last_name = request.form["last_name"]
        user = User(username, first_name, last_name, pref_name, email)
        user.set_password(password)
        user = user.save()
        login_user(user)
        if not next_page or url_parse(next_page).netloc != "":
            return redirect(url_for("dashboard.reroute"))
        return redirect(next_page)
    return render_template("auth/register.html", form=form, title="Register",
                           page="register", next=next_page, user=current_user)


@auth.route("/test")
def test():
    text = f"<h1>Current user authenticated?: {current_user.is_authenticated}</h1>"
    if current_user.is_authenticated:
        text = text + f"<h2>Logged in as: {current_user.id}</h2>"
    return text

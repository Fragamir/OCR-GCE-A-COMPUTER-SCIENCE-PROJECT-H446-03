from flask import Blueprint, render_template, send_from_directory
from flask_login import current_user
import os

main = Blueprint("main", __name__, template_folder="templates", static_folder="static")


@main.route("/")
def index():
    return render_template("index.html", user=current_user, title="Welcome")


@main.route("/Conduit.exe")
def client_script():
    return send_from_directory(os.path.join(main.root_path, "../../static"),
                               "Conduit.exe",
                               mimetype="application/vnd.microsoft.portable-executable")

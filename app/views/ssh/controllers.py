from flask import Blueprint

ssh = Blueprint("ssh", __name__, template_folder="templates", static_folder="static")


from flask import Blueprint, render_template, abort, redirect, url_for, request
from flask_login import current_user, login_required
from app.models import Machine, User, users_machines
from functools import wraps
from json import dumps
from time import sleep

dashboard = Blueprint("dashboard", __name__, template_folder="templates", static_folder="../../static")


def locked_view(func):
    @wraps(func)
    def decorated_view(*args, **kwargs):
        userid = None
        path_split = request.path.split("/")
        for idx, val in enumerate(path_split):
            if val == "u":
                userid = path_split[idx + 1]
                break
            if val == "m" or val.split("-")[0] == "m":
                machine_id = path_split[idx + 1]
                if current_user.is_authenticated:
                    if not User.query().join(users_machines) \
                            .join(Machine) \
                            .filter(User.id == current_user.id) \
                            .filter(Machine.id == machine_id).all():
                        return abort(401)
                    return func(*args, **kwargs)
                return abort(401)
        try:
            userid = int(userid)
        except ValueError:
            return abort(404)
        if current_user.is_authenticated:
            if int(current_user.id) == int(userid):
                return func(*args, **kwargs)
        return abort(401)

    return decorated_view


@dashboard.route("/")
@login_required
def reroute():
    return redirect(url_for("dashboard.index", userid=current_user.id))  # redirect


@dashboard.route("/accept_pending", methods=["POST"])
def accept_pending():
    m = Machine.query().filter(Machine.id == request.form.get("machine_id")).first()
    if m and str(current_user.id) == request.form.get("user_id"):
        current_user.machines.append(m)
        current_user.update()
        m.update(pending_owner_id=None)
        return dumps("{status: success}")
    return abort(500)


@dashboard.route("/remove_pending", methods=["POST"])
def remove_pending():
    m = Machine.query().filter(Machine.id == request.form.get("machine_id")) \
        .filter(Machine.pending_owner_id == current_user.id).first()
    if m and str(current_user.id) == request.form.get("user_id"):
        m.delete()
        return dumps("{status: success}")
    return abort(500)


@dashboard.route("/u/<userid>")
@locked_view
def index(userid):
    m = Machine.query().join(users_machines).join(User) \
        .filter(User.id == userid).all()
    return render_template("dashboard/dashboard.html", title="Dashboard",
                           user=current_user, machines=m)


@dashboard.route("/m/<machineid>")
@locked_view
def machine_json(machineid):
    m = Machine.get(machineid)
    if m:
        status = m.sys_status
        return dumps(status)
    else:
        return abort(404)


@dashboard.route("/m-more/<machineid>")
@locked_view
def machine_more(machineid):
    m = Machine.get(machineid)
    if not m.nickname == "":
        title = f"Machine (#{m.id}): {m.nickname}"
    else:
        title = f"Machine: #{m.id}"
    u = User.query().join(users_machines) \
        .join(Machine).filter(Machine.id == machineid).all()
    return render_template("dashboard/machine.html", m=m, u=u,
                           user=current_user, title=title)


@dashboard.route("/m-more/<machineid>/command", methods=["POST"])
@locked_view
def machine_command(machineid):
    m = Machine.get(machineid)
    command = request.form.get("data")
    m.command = command
    while True:
        for out in m.output:
            if out[0] == command:
                if out[:4] == "<br>":
                    out = out[4:]
                return {"output": out[1].replace("\r\n", "<br>")
                        .replace("\n", "<br>").replace("\r", "<br>")}, 200
        sleep(1)
        m = m.update()


@dashboard.route("/m-more/<machineid>/add_user", methods=["POST"])
@locked_view
def machine_add_user(machineid):
    username = request.form.get("data")
    user = User.query() \
        .filter(User.username == username).first()
    if not user:
        return {"error": f"Error: User with username '{username}' does not exist."}, 415
    machine = Machine.get(machineid)
    for m in user.machines:
        if machine.id == m.id:
            return {"error": "Error: This user already has access to this machine."}, 415
    user.machines.append(machine)
    user.save()
    return {"username": username}, 200

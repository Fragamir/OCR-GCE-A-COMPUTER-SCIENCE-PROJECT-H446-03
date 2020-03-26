from app import db, login_manager, get_config_value
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy.ext.hybrid import hybrid_property
import json


@login_manager.user_loader
def load_user(user_id):
    return User.get(int(user_id))  # used by flask-login when current_user is called


users_machines = db.Table(
    "users_machines",
    db.Column("user_id", db.Integer, db.ForeignKey("user.id"), nullable=False),
    db.Column("machine_id", db.Integer, db.ForeignKey("machine.id"), nullable=False),
    db.PrimaryKeyConstraint("user_id", "machine_id")
)


class User(UserMixin, db.Model):
    __tablename__ = "user"

    id = db.Column(db.Integer,
                   primary_key=True)

    username = db.Column(db.String(32),
                         nullable=False,
                         unique=True)

    first_name = db.Column(db.String(100),
                           nullable=False,
                           unique=False)

    last_name = db.Column(db.String(32),
                          nullable=False,
                          unique=False)

    pref_name = db.Column(db.String(32),
                          nullable=True,
                          unique=False)

    email = db.Column(db.String(100),
                      nullable=False,
                      unique=True)

    pwhash = db.Column(db.String(100),
                       unique=False)

    admin = db.Column(db.Boolean,
                      default=False)

    pending_machines = db.relationship("Machine", back_populates="pending_owner")

    machines = db.relationship("Machine", secondary=users_machines,
                               backref="users")

    def __init__(self, username, first_name, last_name, pref_name, email):
        self.username = username
        self.first_name = first_name
        self.last_name = last_name
        self.email = email
        if pref_name == "":
            pref_name = first_name
        self.pref_name = pref_name

    def set_password(self, password):
        self.pwhash = generate_password_hash(password, method="md5")  # Change method

    def check_password(self, password):
        return check_password_hash(self.pwhash, password)

    def __repr__(self):
        return f"<User {self.id} : '{self.username}'>"


class Machine(db.Model):
    __tablename__ = "machine"

    id = db.Column(db.Integer,
                   primary_key=True)

    nickname = db.Column(db.String(32),
                         nullable=True,
                         unique=False)

    mac_address = db.Column(db.String(17),
                            unique=True,
                            nullable=False)

    last_seen = db.Column(db.DateTime(),
                          nullable=True)

    __sys_details = db.Column(db.String)

    __sys_status = db.Column(db.String)

    secret_key = db.Column(db.String)

    pending_owner_id = db.Column(db.Integer,
                                 db.ForeignKey("user.id"),
                                 nullable=True)

    pending_owner = db.relationship("User",
                                    back_populates="pending_machines")

    __commands = db.Column(db.String,
                           default="",
                           nullable=True)

    __output = db.Column(db.String,
                         default="",
                         nullable=True)

    @hybrid_property
    def output(self):
        if self.__output == "":
            return ""
        return [x[2:].split(",") for x in self.__output.split(";")]

    @output.setter
    def output(self, value):
        if not self.__output == "":
            self.__output += f";'{value}'"
        else:
            self.__output = f"'{value}'"
        if len(self.__output.split(";")) > get_config_value("OUT_MAX", 10):
            del self.output
        self.save()

    @output.deleter
    def output(self):
        self.__output = self.__output[len(self.__output.split(";")[0])+1:]
        self.save()

    @hybrid_property
    def command(self):
        if self.__commands == "":
            return ""
        return eval(self.__commands.split(";")[0])

    @command.setter
    def command(self, value):
        if not self.__commands == "":
            self.__commands += f";'{value}'"
        else:
            self.__commands = f"'{value}'"
        if len(self.__commands.split(";")) > get_config_value("COM_MAX", 10):
            del self.command
        self.save()

    @command.deleter
    def command(self):
        self.__commands = self.__commands[len(self.__commands.split(";")[0])+1:]
        self.save()

    @hybrid_property
    def sys_details(self):
        return json.loads(self.__sys_details)

    @sys_details.setter
    def sys_details(self, value):
        self.__sys_details = json.dumps(value)
        self.save()

    @hybrid_property
    def sys_status(self):
        status = []
        if not self.__sys_status == "":
            for item in self.__sys_status.split(";"):
                status.append(eval(eval(item)))
        return status

    @sys_status.setter
    def sys_status(self, value):
        instance = str(value).replace("[", '"').replace("]", '"').replace(", ", ',')
        if self.__sys_status:
            new_status = self.__sys_status + ";" + instance
        else:
            new_status = instance
        if len(new_status.split(";")) > get_config_value("STATUS_MAX", 10):
            new_status = new_status[len(new_status.split(";")[0]) + 1:]
        self.__sys_status = new_status
        self.save()

    def __init__(self, mac_address, pending_owner_id, nickname=None):
        if nickname:
            self.nickname = nickname
        self.mac_address = mac_address
        self.pending_owner_id = pending_owner_id
        self.__sys_status = ""
        self.__sys_details = "{}"

    def __repr__(self):
        return f"<Machine {self.id}>"


db.create_all()

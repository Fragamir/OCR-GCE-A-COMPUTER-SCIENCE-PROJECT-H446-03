from flask import Flask, send_from_directory
from active_alchemy import ActiveAlchemy
from flask_login import LoginManager
import os
import sys


# Globally accessible variables
db = ActiveAlchemy("sqlite:///Conduit.db?check_same_thread=False")
login_manager = LoginManager()
app_config = {}


def get_config_value(item, default=None):
    global app_config
    return app_config.get(item, default)


def parse_port(port, config=None):
    try:
        int(port)
    except ValueError:
        if port == "cfg" and config:
            port = config.get("socket_port", None)
            port = parse_port(port)
        else:
            return False
    return port


def create_app(config="Production", socket_port=None):
    global app_config
    # Initialise core flask app and apply config:
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_pyfile(f'{config}.cfg')
    app_config = app.config
    print(f'Initialised flask app with config \"{config}\"')

    # Initialise plugins:
    db.init_app(app)
    login_manager.init_app(app)

    if socket_port:
        port = parse_port(socket_port, app.config)
        if port:
            from app.sockets import server_thread_getter
            server_thread = server_thread_getter(socket_port)
            server_thread.start()
        else:
            print(f"\n\n\nError parsing port\n\n\n")

    # Use context to register blueprints:
    with app.app_context():

        if len(sys.argv) > 2:
            for argument in sys.argv[1:]:
                if argument == "--clear_db":
                    db.drop_all()
                    db.create_all()
        
        @app.route("/favicon.ico")
        def favicon():
            return send_from_directory(os.path.join(app.root_path, "static"),
                                       "favicon.ico", mimetype="image/vnd.microsoft.icon")

        print(f"Server started.\nImporting blueprints...")

        from app.views.main.controllers import main as main_bp
        from app.views.admin.controllers import admin as admin_bp
        from app.views.dashboard.controllers import dashboard as dashboard_bp
        from app.views.auth.controllers import auth as auth_bp
        from app.views.ssh.controllers import ssh as ssh_bp

        print(f"Blueprints imported.\nRegistering blueprints...")

        app.register_blueprint(main_bp, url_prefix='/')
        app.register_blueprint(admin_bp, url_prefix="/admin")
        app.register_blueprint(dashboard_bp, url_prefix="/dashboard")
        app.register_blueprint(auth_bp, url_prefix="/auth")
        app.register_blueprint(ssh_bp, url_prefix="/ssh")

        print(f"Blueprints registered.")

        login_manager.login_view = "auth.login"
        login_manager.login_message = "Please login"

        return app

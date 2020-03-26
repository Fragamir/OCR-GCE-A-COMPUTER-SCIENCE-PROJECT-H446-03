from app import create_app

app = create_app("Production", 16969)
app.run(port=80, host="0.0.0.0", use_reloader=False)  # use_reloader MUST be false or it binds twice to the socket port

"""Entry point for user-service.

Run with:
    python -m app                      # uses environment variables
    PORT=8080 python -m app            # custom port

Debug mode and the reloader are always disabled regardless of environment
variables such as FLASK_DEBUG (REQ-USR-09).
"""
import socket

from werkzeug.serving import make_server

from app import create_app
from app.config import load_config

if __name__ == "__main__":
    cfg = load_config()
    application = create_app(cfg)
    application.debug = False
    host, port = "127.0.0.1", cfg["PORT"]
    # A pre-bound socket avoids HTTPServer.server_bind's blocking reverse DNS lookup.
    with socket.create_server((host, port)) as listener:
        with make_server(host, port, application, threaded=True, fd=listener.fileno()) as server:
            server.serve_forever()

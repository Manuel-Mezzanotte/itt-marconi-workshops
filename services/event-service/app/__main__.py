import socket

from werkzeug.serving import make_server

from app import create_app


if __name__ == "__main__":
    application = create_app()
    application.debug = False
    host, port = "127.0.0.1", application.config["EVENT_SERVICE_CONFIG"]["PORT"]
    with socket.create_server((host, port)) as listener:
        with make_server(host, port, application, threaded=True, fd=listener.fileno()) as server:
            server.serve_forever()

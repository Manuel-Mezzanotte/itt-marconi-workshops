"""Entry point for user-service.

Run with:
    python -m app                      # uses environment variables
    PORT=8080 python -m app            # custom port

No debug mode, no reloader — production-safe startup.
"""
from app import create_app
from app.config import load_config

if __name__ == "__main__":
    cfg = load_config()
    application = create_app()
    application.run(host="127.0.0.1", port=cfg["PORT"])

"""Application factory for user-service.

Usage::

    from app import create_app
    app = create_app()          # reads os.environ
    app = create_app({"PORT": 9000, "STORAGE_BACKEND": "memory"})  # test overrides
"""
from __future__ import annotations

from typing import Any

from flask import Blueprint, Flask, jsonify

from app.config import load_config
from app.errors import register_error_handlers
from app.repositories import get_repository
from app.routes import create_routes_blueprint
from app.service import UserService


def create_app(config: dict[str, Any] | None = None) -> Flask:
    """Create and configure the Flask application.

    Parameters
    ----------
    config:
        Optional dict of configuration overrides passed to load_config().
        Each call to create_app() produces an independent application with
        its own configuration, repositories and service.

    Returns
    -------
    Flask application instance, fully configured and ready to serve.
    """
    cfg = load_config(config)

    app = Flask(__name__)
    app.config["USER_SERVICE_CONFIG"] = cfg

    # Register error handlers at application level.
    register_error_handlers(app)

    # Health blueprint
    health_bp = Blueprint("health", __name__)

    @health_bp.route("/health", methods=["GET"])
    def health():
        """REQ-USR-07: health check, no storage involved."""
        return jsonify({"status": "ok", "service": "user-service"}), 200

    app.register_blueprint(health_bp)

    # Initialize repository and service
    repository = get_repository(cfg["STORAGE_BACKEND"], cfg["DATA_DIR"])
    service = UserService(repository)

    # Register routes blueprint
    routes_bp = create_routes_blueprint(service)
    app.register_blueprint(routes_bp)

    return app

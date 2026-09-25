from flask import Flask, jsonify

from app.config import load_config
from app.errors import register_error_handlers


def create_app(config=None):
    application = Flask(__name__)
    application.config["EVENT_SERVICE_CONFIG"] = load_config(config)
    register_error_handlers(application)

    @application.get("/health")
    def health():
        return jsonify(status="ok", service="event-service")

    return application

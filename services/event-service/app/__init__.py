from flask import Flask, jsonify

from app.config import load_config
from app.errors import register_error_handlers
from app.clients import UserClient
from app.repositories import get_repository
from app.routes import create_routes
from app.service import EventService


def create_app(config=None):
    application = Flask(__name__)
    config = load_config(config)
    application.config["EVENT_SERVICE_CONFIG"] = config
    register_error_handlers(application)

    @application.get("/health")
    def health():
        return jsonify(status="ok", service="event-service")

    repository = get_repository(config["STORAGE_BACKEND"], config["DATA_DIR"])
    service = EventService(repository, UserClient(config["USER_SERVICE_URL"]))
    application.extensions["event_repository"] = repository
    application.extensions["event_service"] = service
    application.register_blueprint(create_routes(service))
    return application

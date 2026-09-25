from flask import Flask, jsonify

from app.config import load_config
from app.errors import register_error_handlers
from app.clients import ReferenceClients
from app.repositories import get_repository
from app.routes import create_routes
from app.service import RegistrationService


def create_app(config=None):
    application = Flask(__name__)
    config = load_config(config)
    application.config["REGISTRATION_SERVICE_CONFIG"] = config
    register_error_handlers(application)

    @application.get("/health")
    def health():
        return jsonify(status="ok", service="registration-service")

    repository = get_repository(config["STORAGE_BACKEND"], config["DATA_DIR"])
    references = ReferenceClients(config["USER_SERVICE_URL"], config["EVENT_SERVICE_URL"])
    service = RegistrationService(repository, references)
    application.extensions["registration_repository"] = repository
    application.extensions["registration_service"] = service
    application.register_blueprint(create_routes(service))
    return application

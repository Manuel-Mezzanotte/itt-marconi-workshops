from flask import Blueprint, jsonify, request


def create_routes(service):
    routes = Blueprint("registrations", __name__, url_prefix="/api/v1/registrations")

    @routes.post("")
    def create():
        registration = service.create(request.get_json(silent=False))
        return jsonify(registration), 201, {
            "Location": f"/api/v1/registrations/{registration['id']}",
        }

    return routes

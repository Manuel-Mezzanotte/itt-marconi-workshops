from flask import Blueprint, jsonify, request


def create_routes(service):
    routes = Blueprint("events", __name__, url_prefix="/api/v1/events")

    @routes.post("")
    def create():
        event = service.create(request.get_json(silent=False))
        return jsonify(event), 201, {"Location": f"/api/v1/events/{event['id']}"}

    return routes

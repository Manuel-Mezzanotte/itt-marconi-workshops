from flask import Blueprint, jsonify, request


def create_routes(service):
    routes = Blueprint("registrations", __name__, url_prefix="/api/v1/registrations")

    @routes.post("")
    def create():
        registration = service.create(request.get_json(silent=False))
        return jsonify(registration), 201, {
            "Location": f"/api/v1/registrations/{registration['id']}",
        }

    @routes.get("")
    def list_registrations():
        return jsonify(service.list(**{
            field: request.args.get(field)
            for field in ("page", "page_size", "user_id", "event_id", "status")
        }))

    @routes.get("/stats")
    def stats():
        return jsonify(service.stats(request.args.get("event_id")))

    @routes.get("/<registration_id>")
    def get_registration(registration_id):
        return jsonify(service.get(registration_id))

    return routes

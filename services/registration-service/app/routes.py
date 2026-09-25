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

    @routes.patch("/<registration_id>")
    def patch_registration(registration_id):
        return jsonify(service.patch(registration_id, request.get_json(silent=False)))

    @routes.delete("/<registration_id>")
    def delete_registration(registration_id):
        service.delete(registration_id)
        return "", 204

    return routes

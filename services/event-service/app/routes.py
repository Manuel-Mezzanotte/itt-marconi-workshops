from flask import Blueprint, jsonify, request


def create_routes(service):
    routes = Blueprint("events", __name__, url_prefix="/api/v1/events")

    @routes.post("")
    def create():
        event = service.create(request.get_json(silent=False))
        return jsonify(event), 201, {"Location": f"/api/v1/events/{event['id']}"}

    @routes.get("")
    def list_events():
        return jsonify(service.list(
            page=request.args.get("page"), page_size=request.args.get("page_size"),
            status=request.args.get("status"), city=request.args.get("city"),
        ))

    @routes.get("/<event_id>")
    def get_event(event_id):
        return jsonify(service.get(event_id))

    @routes.put("/<event_id>")
    def replace_event(event_id):
        return jsonify(service.replace(event_id, request.get_json(silent=False)))

    @routes.patch("/<event_id>")
    def patch_event(event_id):
        return jsonify(service.patch(event_id, request.get_json(silent=False)))

    @routes.delete("/<event_id>")
    def delete_event(event_id):
        service.delete(event_id)
        return "", 204

    return routes

"""HTTP routes for user-service.

Handles request parsing, response formatting, and HTTP semantics.
Business logic is delegated to UserService.
"""
from __future__ import annotations

from flask import Blueprint, jsonify, request

from app.errors import ValidationError
from app.service import UserService


def create_routes_blueprint(service: UserService) -> Blueprint:
    """Create and return the routes blueprint.

    Parameters
    ----------
    service:
        UserService instance to delegate business logic.

    Returns
    -------
    Flask Blueprint with all user routes.
    """
    bp = Blueprint("users", __name__, url_prefix="/api/v1")

    @bp.route("/users", methods=["POST"])
    def create_user():
        """POST /api/v1/users: create a new user.

        Request body: UserCreate (JSON object).
        Response: 201 with Location header and User record.
        """
        # Parse JSON; silent=False returns None for valid non-object JSON
        data = request.get_json(silent=False, force=False)

        # If data is valid JSON but not an object (null, array, scalar),
        # treat as a validation error
        if data is None:
            raise ValidationError(
                "Request body must be a JSON object",
                {"given": "null"},
            )
        if not isinstance(data, dict):
            raise ValidationError(
                "Request body must be a JSON object",
                {"given": type(data).__name__},
            )

        # Create the user
        user = service.create_user(data)

        # Response: 201 Created with Location header (relative path per design)
        location = f"/api/v1/users/{user['id']}"
        return jsonify(user), 201, {"Location": location}

    @bp.route("/users", methods=["GET"])
    def list_users():
        return jsonify(service.list_users(
            role=request.args.get("role"),
            email=request.args.get("email"),
            page=request.args.get("page"),
            page_size=request.args.get("page_size"),
        ))

    @bp.route("/users/<user_id>", methods=["GET"])
    def get_user(user_id):
        return jsonify(service.get_user(user_id))

    @bp.route("/users/<user_id>", methods=["PUT"])
    def replace_user(user_id):
        return jsonify(service.replace_user(user_id, request.get_json(silent=False)))

    @bp.route("/users/<user_id>", methods=["PATCH"])
    def update_user(user_id):
        return jsonify(service.update_user(user_id, request.get_json(silent=False)))

    return bp

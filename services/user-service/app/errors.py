"""Domain exceptions and Flask error handlers for user-service.

All HTTP error responses use the uniform format:
  {"error": {"code": "UPPER_SNAKE", "message": "...", "details": {}}}

Handler registration is done in create_app() via register_error_handlers().
"""
from __future__ import annotations

from flask import Flask, jsonify
from werkzeug.exceptions import MethodNotAllowed, NotFound


# ---------------------------------------------------------------------------
# Domain exceptions
# ---------------------------------------------------------------------------


class ValidationError(Exception):
    """Raised when input data fails validation (→ 422 VALIDATION_ERROR)."""

    def __init__(self, message: str = "Validation error", details: dict | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.details = details or {}


class UserNotFound(Exception):
    """Raised when a requested user does not exist (→ 404 NOT_FOUND)."""

    def __init__(self, user_id: str = "") -> None:
        super().__init__(f"User not found: {user_id}")
        self.user_id = user_id


class EmailAlreadyExists(Exception):
    """Raised when an email is already in use (→ 409 EMAIL_ALREADY_EXISTS)."""

    def __init__(self, email: str = "") -> None:
        super().__init__(f"Email already exists: {email}")
        self.email = email


# ---------------------------------------------------------------------------
# Error response builder
# ---------------------------------------------------------------------------


def _error_response(code: str, message: str, status: int, details: dict | None = None):
    body = {
        "error": {
            "code": code,
            "message": message,
            "details": details or {},
        }
    }
    return jsonify(body), status


# ---------------------------------------------------------------------------
# Handler registration
# ---------------------------------------------------------------------------


def register_error_handlers(app: Flask) -> None:
    """Attach all error handlers to *app* at application level."""

    @app.errorhandler(400)
    def handle_bad_request(exc):
        return _error_response("MALFORMED_JSON", str(exc), 400)

    @app.errorhandler(415)
    def handle_unsupported_media_type(exc):
        """Issue #4: UnsupportedMediaType must return 400 MALFORMED_JSON as JSON."""
        return _error_response("MALFORMED_JSON", str(exc), 400)

    @app.errorhandler(404)
    def handle_not_found(exc):
        return _error_response("NOT_FOUND", str(exc), 404)

    @app.errorhandler(405)
    def handle_method_not_allowed(exc):
        return _error_response("METHOD_NOT_ALLOWED", str(exc), 405)

    @app.errorhandler(ValidationError)
    def handle_validation_error(exc: ValidationError):
        return _error_response("VALIDATION_ERROR", exc.message, 422, exc.details)

    @app.errorhandler(UserNotFound)
    def handle_user_not_found(exc: UserNotFound):
        return _error_response("NOT_FOUND", str(exc), 404)

    @app.errorhandler(EmailAlreadyExists)
    def handle_email_already_exists(exc: EmailAlreadyExists):
        return _error_response("EMAIL_ALREADY_EXISTS", str(exc), 409)

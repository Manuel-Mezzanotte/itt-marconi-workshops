from flask import jsonify
from werkzeug.exceptions import HTTPException


class ApiError(Exception):
    def __init__(self, status, code, message, details=None):
        super().__init__(message)
        self.status = status
        self.code = code
        self.details = details or {}


def register_error_handlers(app):
    @app.errorhandler(ApiError)
    def domain_error(exc):
        return jsonify(error={
            "code": exc.code, "message": str(exc), "details": exc.details,
        }), exc.status

    @app.errorhandler(HTTPException)
    def http_error(exc):
        status, code = {
            400: (400, "MALFORMED_JSON"),
            415: (400, "MALFORMED_JSON"),
            404: (404, "NOT_FOUND"),
            405: (405, "METHOD_NOT_ALLOWED"),
            500: (500, "INTERNAL_ERROR"),
        }.get(exc.code, (exc.code, "HTTP_ERROR"))
        return jsonify(error={"code": code, "message": exc.name, "details": {}}), status

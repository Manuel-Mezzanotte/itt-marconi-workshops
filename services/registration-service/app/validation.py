import re
from uuid import UUID

from app.errors import ApiError


def invalid(message, **details):
    raise ApiError(422, "VALIDATION_ERROR", message, details)


def validate_uuid(value, field):
    if not isinstance(value, str) or not re.fullmatch(
        r"[0-9a-fA-F]{8}(-[0-9a-fA-F]{4}){3}-[0-9a-fA-F]{12}", value,
    ):
        invalid("Expected a UUID", field=field)
    return str(UUID(value))


def validate_create(data):
    fields = {"user_id", "event_id"}
    if not isinstance(data, dict) or set(data) != fields:
        invalid("Body must contain only user_id and event_id")
    return {field: validate_uuid(data[field], field) for field in sorted(fields)}


def validate_patch(data):
    if not isinstance(data, dict) or set(data) != {"status"}:
        invalid("Body must contain only status")
    status = data["status"]
    if not isinstance(status, str) or status not in {"confirmed", "cancelled"}:
        invalid("Invalid registration status", field="status")
    return status

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


def validate_query(page=None, page_size=None, user_id=None, event_id=None, status=None):
    numbers = []
    for name, raw, default in (("page", page, 1), ("page_size", page_size, 20)):
        try:
            value = default if raw is None else int(raw)
        except (ValueError, TypeError):
            invalid("Pagination must use integers", field=name)
        if value < 1 or (name == "page_size" and value > 100):
            invalid("Pagination outside allowed range", field=name)
        numbers.append(value)
    filters = {}
    for field, value in (("user_id", user_id), ("event_id", event_id)):
        if value is not None:
            filters[field] = validate_uuid(value, field)
    if status is not None:
        if status not in {"confirmed", "cancelled"}:
            invalid("Invalid status filter", field="status")
        filters["status"] = status
    return numbers[0], numbers[1], filters

import math
import re
from datetime import date
from decimal import Decimal, ROUND_HALF_UP, localcontext
from uuid import UUID

from app.errors import ApiError


STATUSES = {"draft", "published", "cancelled"}
REQUIRED = {"title", "organizer_id", "venue", "city", "start_date", "end_date", "capacity", "price"}
FIELDS = REQUIRED | {"description", "status"}
TEXT_LIMITS = {"title": (3, 120), "description": (0, 2000), "venue": (0, 100), "city": (0, 60)}


def invalid(message, **details):
    raise ApiError(422, "VALIDATION_ERROR", message, details)


def validate_event(data, partial=False):
    if not isinstance(data, dict):
        invalid("Body must be a JSON object")
    if set(data) - FIELDS:
        invalid("Unexpected fields", fields=sorted(set(data) - FIELDS))
    if not partial and REQUIRED - set(data):
        invalid("Missing required fields", fields=sorted(REQUIRED - set(data)))
    result = {}
    for field, value in data.items():
        if field == "description" and value is None:
            result[field] = None
            continue
        if field in TEXT_LIMITS:
            minimum, maximum = TEXT_LIMITS[field]
            if not isinstance(value, str) or not minimum <= len(value) <= maximum:
                invalid("Invalid string length or type", field=field)
        elif field == "organizer_id":
            if not isinstance(value, str) or not re.fullmatch(
                r"[0-9a-fA-F]{8}(-[0-9a-fA-F]{4}){3}-[0-9a-fA-F]{12}", value,
            ):
                invalid("organizer_id must be a UUID", field=field)
            value = str(UUID(value))
        elif field in {"start_date", "end_date"}:
            if not isinstance(value, str) or not re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
                invalid("Date must use YYYY-MM-DD", field=field)
            try:
                date.fromisoformat(value)
            except ValueError:
                invalid("Invalid calendar date", field=field)
        elif field == "capacity":
            if type(value) is not int or not 1 <= value <= 10000:
                invalid("capacity must be an integer between 1 and 10000", field=field)
        elif field == "price":
            if type(value) not in (int, float) or value < 0:
                invalid("price must be a non-negative number", field=field)
            try:
                finite = math.isfinite(value)
            except OverflowError:
                finite = False
            if not finite:
                invalid("price must be finite", field=field)
            amount = Decimal(str(value))
            with localcontext() as context:
                context.prec = max(28, len(amount.as_tuple().digits) + max(amount.adjusted(), 0) + 3)
                value = float(amount.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))
        elif field == "status":
            if not isinstance(value, str) or value not in STATUSES:
                invalid("Invalid event status", field=field)
        result[field] = value
    if not partial:
        result.setdefault("description", None)
        result.setdefault("status", "draft")
        validate_dates(result)
    return result


def validate_dates(record):
    if record["end_date"] < record["start_date"]:
        invalid("end_date must not precede start_date", field="end_date")


def validate_transition(previous, target):
    allowed = {("draft", "published"), ("draft", "cancelled"), ("published", "cancelled")}
    if previous != target and (previous, target) not in allowed:
        raise ApiError(422, "INVALID_STATUS_TRANSITION", "Event status transition is not allowed",
                       {"from": previous, "to": target})

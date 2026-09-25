from datetime import datetime, timezone
from uuid import uuid4

from app.errors import ApiError
from app.repositories import RegistrationRepository
from app.validation import validate_create, validate_query, validate_uuid


def timestamp():
    return datetime.now(timezone.utc).isoformat(timespec="microseconds").replace("+00:00", "Z")


class RegistrationService:
    def __init__(self, repository: RegistrationRepository, references):
        self.repository = repository
        self.references = references

    def create(self, data):
        validated = validate_create(data)
        self.references.get_user(validated["user_id"])
        event = self.references.get_event(validated["event_id"])
        if event["status"] != "published":
            raise ApiError(422, "EVENT_NOT_OPEN", "Event must be published")
        now = timestamp()
        record = {
            **validated, "id": str(uuid4()), "amount": event["price"], "status": "confirmed",
            "created_at": now, "updated_at": now,
        }
        return self.repository.reserve(record, event["capacity"])

    def get(self, registration_id):
        registration = self.repository.get(registration_id)
        if registration is None:
            raise ApiError(404, "NOT_FOUND", "Registration does not exist")
        return registration

    def list(self, **query):
        page, size, filters = validate_query(**query)
        items, total = self.repository.list(filters, page, size)
        return {"items": items, "page": page, "page_size": size, "total": total}

    def stats(self, event_id):
        event_id = validate_uuid(event_id, "event_id")
        event = self.references.get_event(event_id, missing_status=404)
        confirmed = self.repository.count_confirmed(event_id)
        return {
            "event_id": event_id, "capacity": event["capacity"],
            "confirmed": confirmed, "available": max(0, event["capacity"] - confirmed),
        }

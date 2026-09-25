from datetime import datetime, timezone
from uuid import uuid4

from app.errors import ApiError
from app.repositories import RegistrationRepository
from app.validation import validate_create


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

from datetime import datetime, timezone
from uuid import uuid4

from app.repositories import EventRepository
from app.validation import validate_event


def timestamp():
    return datetime.now(timezone.utc).isoformat(timespec="microseconds").replace("+00:00", "Z")


class EventService:
    def __init__(self, repository: EventRepository, user_client):
        self.repository = repository
        self.user_client = user_client

    def create(self, data):
        validated = validate_event(data)
        self.user_client.require_organizer(validated["organizer_id"])
        now = timestamp()
        return self.repository.create({
            **validated, "id": str(uuid4()), "created_at": now, "updated_at": now,
        })

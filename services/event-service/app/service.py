from datetime import datetime, timezone
from uuid import uuid4

from app.repositories import EventRepository
from app.errors import ApiError
from app.validation import validate_event, validate_query


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

    def get(self, event_id):
        event = self.repository.get(event_id)
        if event is None:
            raise ApiError(404, "NOT_FOUND", "Event does not exist")
        return event

    def list(self, page=None, page_size=None, status=None, city=None):
        page, size, filters = validate_query(page, page_size, status, city)
        items, total = self.repository.list(filters, page, size)
        return {"items": items, "page": page, "page_size": size, "total": total}

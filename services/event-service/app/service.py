from datetime import datetime, timezone
from uuid import uuid4

from app.repositories import EventRepository
from app.errors import ApiError
from app.validation import validate_dates, validate_event, validate_query, validate_transition


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

    def replace(self, event_id, data):
        self.get(event_id)
        changes = validate_event(data)
        self.user_client.require_organizer(changes["organizer_id"])
        return self._save_changes(event_id, changes, replace=True)

    def patch(self, event_id, data):
        current = self.get(event_id)
        changes = validate_event(data, partial=True)
        if not changes:
            return current
        if "organizer_id" in changes:
            self.user_client.require_organizer(changes["organizer_id"])
        return self._save_changes(event_id, changes)

    def _save_changes(self, event_id, changes, replace=False):
        def transform(current):
            updated = {**({} if replace else current), **changes}
            validate_dates(updated)
            validate_transition(current["status"], updated["status"])
            return {
                **updated, "id": current["id"], "created_at": current["created_at"],
                "updated_at": timestamp(),
            }

        updated = self.repository.update(event_id, transform)
        if updated is None:
            raise ApiError(404, "NOT_FOUND", "Event does not exist")
        return updated

    def delete(self, event_id):
        if not self.repository.delete(event_id):
            raise ApiError(404, "NOT_FOUND", "Event does not exist")

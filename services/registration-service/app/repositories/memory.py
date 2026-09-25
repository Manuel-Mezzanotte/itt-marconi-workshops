from copy import deepcopy
from threading import RLock

from app.repositories import change_status, check_slot, paginate


class MemoryRepository:
    def __init__(self):
        self._records = {}
        self._lock = RLock()

    def _read(self):
        return deepcopy(self._records)

    def _write(self, records):
        self._records = deepcopy(records)

    def reserve(self, record, capacity):
        with self._lock:
            records = self._read()
            confirmed = [item for item in records.values()
                         if item["event_id"] == record["event_id"] and item["status"] == "confirmed"]
            check_slot(any(item["user_id"] == record["user_id"] for item in confirmed),
                       len(confirmed), capacity)
            if record["id"] in records:
                raise ValueError("Duplicate registration id")
            records[record["id"]] = deepcopy(record)
            self._write(records)
            return deepcopy(record)

    def get(self, registration_id):
        with self._lock:
            return deepcopy(self._read().get(registration_id))

    def list(self, filters, page, page_size):
        with self._lock:
            return paginate(self._read().values(), filters, page, page_size)

    def count_confirmed(self, event_id):
        with self._lock:
            return sum(item["event_id"] == event_id and item["status"] == "confirmed"
                       for item in self._read().values())

    def update_status(self, registration_id, status, updated_at):
        with self._lock:
            records = self._read()
            current = records.get(registration_id)
            if current is None:
                return None
            updated = change_status(current, status, updated_at)
            if updated != current:
                records[registration_id] = updated
                self._write(records)
            return deepcopy(updated)

    def delete(self, registration_id):
        with self._lock:
            records = self._read()
            if registration_id not in records:
                return False
            del records[registration_id]
            self._write(records)
            return True

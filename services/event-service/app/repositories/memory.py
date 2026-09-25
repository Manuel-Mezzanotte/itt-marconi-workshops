from copy import deepcopy
from threading import RLock

from app.repositories import paginate


class MemoryRepository:
    def __init__(self):
        self._lock = RLock()
        self._records = {}

    def _read(self):
        return deepcopy(self._records)

    def _write(self, records):
        self._records = deepcopy(records)

    def create(self, record):
        with self._lock:
            records = self._read()
            if record["id"] in records:
                raise ValueError("Duplicate event id")
            records[record["id"]] = deepcopy(record)
            self._write(records)
            return deepcopy(record)

    def get(self, event_id):
        with self._lock:
            return deepcopy(self._read().get(event_id))

    def list(self, filters, page, page_size):
        with self._lock:
            return paginate(self._read().values(), filters, page, page_size)

    def update(self, event_id, transform):
        with self._lock:
            records = self._read()
            if event_id not in records:
                return None
            updated = transform(deepcopy(records[event_id]))
            records[event_id] = deepcopy(updated)
            self._write(records)
            return deepcopy(updated)

    def delete(self, event_id):
        with self._lock:
            records = self._read()
            if event_id not in records:
                return False
            del records[event_id]
            self._write(records)
            return True

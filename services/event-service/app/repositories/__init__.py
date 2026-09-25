from copy import deepcopy
from typing import Callable, Protocol


class EventRepository(Protocol):
    def create(self, record: dict) -> dict: ...
    def get(self, event_id: str) -> dict | None: ...
    def list(self, filters: dict, page: int, page_size: int) -> tuple[list, int]: ...
    def update(self, event_id: str, transform: Callable[[dict], dict]) -> dict | None: ...
    def delete(self, event_id: str) -> bool: ...


def paginate(records, filters, page, page_size):
    selected = [
        record for record in records
        if all(record[key] == value for key, value in filters.items() if value is not None)
    ]
    selected.sort(key=lambda record: (record["created_at"], record["id"]))
    offset = (page - 1) * page_size
    return deepcopy(selected[offset:offset + page_size]), len(selected)


def get_repository(backend, data_dir):
    from app.repositories.memory import MemoryRepository
    from app.repositories.json_repo import JsonRepository
    from app.repositories.sqlite_repo import SqliteRepository

    if backend == "memory":
        return MemoryRepository()
    if backend == "json":
        return JsonRepository(data_dir)
    if backend == "sqlite":
        return SqliteRepository(data_dir)
    raise ValueError("Unknown STORAGE_BACKEND")

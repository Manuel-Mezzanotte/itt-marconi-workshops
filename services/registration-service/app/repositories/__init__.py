from copy import deepcopy
from typing import Protocol

from app.errors import ApiError


class RegistrationRepository(Protocol):
    def reserve(self, record: dict, capacity: int) -> dict: ...
    def get(self, registration_id: str) -> dict | None: ...
    def list(self, filters: dict, page: int, page_size: int) -> tuple[list, int]: ...
    def count_confirmed(self, event_id: str) -> int: ...
    def update_status(self, registration_id: str, status: str, updated_at: str) -> dict | None: ...
    def delete(self, registration_id: str) -> bool: ...


def check_slot(duplicate, confirmed, capacity):
    if duplicate:
        raise ApiError(409, "ALREADY_REGISTERED", "User is already registered for this event")
    if confirmed >= capacity:
        raise ApiError(409, "EVENT_FULL", "Event has no available seats")


def change_status(record, status, updated_at):
    if record["status"] == status:
        return record
    if record["status"] == "confirmed" and status == "cancelled":
        return {**record, "status": status, "updated_at": updated_at}
    raise ApiError(422, "INVALID_STATUS_TRANSITION", "Registration cannot be reactivated")


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

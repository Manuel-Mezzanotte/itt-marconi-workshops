"""In-memory UserRepository implementation.

Data is stored in a per-instance dict protected by a threading.RLock.
No global state, no files. A new MemoryRepository instance starts empty.

REQ-USR-09, REQ-USR-12.8 (instance isolation)
REQ-USR-B01 (email uniqueness enforced atomically under the lock)
"""
from __future__ import annotations

import copy
import threading
from typing import Any

from app.errors import EmailAlreadyExists
from app.repositories import UserRepository


class MemoryRepository(UserRepository):
    """Thread-safe in-memory storage for User records.

    All public methods acquire the instance RLock so that read-check-write
    sequences are atomic within a single process.
    """

    def __init__(self) -> None:
        self._store: dict[str, dict[str, Any]] = {}
        self._lock = threading.RLock()

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _find_by_email(self, email: str) -> dict[str, Any] | None:
        """Return the record whose normalised email matches *email*, or None.

        Caller is responsible for holding the lock.
        """
        norm = email.lower()
        for record in self._store.values():
            if record["email"] == norm:
                return record
        return None

    # ------------------------------------------------------------------
    # UserRepository interface
    # ------------------------------------------------------------------

    def create(self, user: dict[str, Any]) -> dict[str, Any]:
        """REQ-USR-B01: atomically check uniqueness and insert."""
        with self._lock:
            existing = self._find_by_email(user["email"])
            if existing is not None:
                raise EmailAlreadyExists(user["email"])
            record = copy.deepcopy(user)
            self._store[record["id"]] = record
            return copy.deepcopy(record)

    def get(self, user_id: str) -> dict[str, Any] | None:
        with self._lock:
            record = self._store.get(user_id)
            return copy.deepcopy(record) if record is not None else None

    def get_by_email(self, email: str) -> dict[str, Any] | None:
        with self._lock:
            record = self._find_by_email(email)
            return copy.deepcopy(record) if record is not None else None

    def list(
        self,
        filters: dict[str, Any],
        page: int,
        page_size: int,
    ) -> tuple[list[dict[str, Any]], int]:
        """REQ-USR-03, REQ-USR-B03: sorted, filtered, paginated list."""
        with self._lock:
            records = list(self._store.values())

        # Apply filters
        role_filter = filters.get("role")
        email_filter = filters.get("email")
        if role_filter is not None:
            records = [r for r in records if r["role"] == role_filter]
        if email_filter is not None:
            norm = email_filter.lower()
            records = [r for r in records if r["email"] == norm]

        # Stable sort: (created_at, id) ascending
        records.sort(key=lambda r: (r["created_at"], r["id"]))

        total = len(records)
        offset = (page - 1) * page_size
        # Guard against enormous offsets
        if offset >= total:
            return [], total
        page_records = records[offset : offset + page_size]
        return [copy.deepcopy(r) for r in page_records], total

    def update(self, user_id: str, user: dict[str, Any]) -> dict[str, Any] | None:
        """REQ-USR-B01: atomically check email uniqueness (excluding own id)."""
        with self._lock:
            if user_id not in self._store:
                return None
            # Check email uniqueness against all other users
            norm_email = user["email"].lower()
            for uid, record in self._store.items():
                if uid != user_id and record["email"] == norm_email:
                    raise EmailAlreadyExists(user["email"])
            updated = copy.deepcopy(user)
            self._store[user_id] = updated
            return copy.deepcopy(updated)

    def delete(self, user_id: str) -> bool:
        with self._lock:
            if user_id not in self._store:
                return False
            del self._store[user_id]
            return True

"""JSON file-based UserRepository implementation.

Data is stored in DATA_DIR/users.json with structure {"users": [...]}.
A per-instance RLock serialises read-check-write sequences within a process.
Writes go to a temporary file and then os.replace() for atomicity: a failure
before the replace does not corrupt the existing data file.

REQ-USR-09.3, REQ-USR-09.7 (persistence across restarts)
REQ-USR-B01 (email uniqueness enforced atomically)
REQ-USR-12.2 (JSON backend)
"""
from __future__ import annotations

import copy
import json
import os
import tempfile
import threading
from pathlib import Path
from typing import Any

from app.errors import EmailAlreadyExists
from app.repositories import UserRepository

_FILENAME = "users.json"


class JsonRepository(UserRepository):
    """Persist User records in a JSON file.

    A single process writer is assumed; the RLock makes in-process operations
    safe but does not guard against concurrent separate processes.
    """

    def __init__(self, data_dir: Path) -> None:
        self._path = Path(data_dir) / _FILENAME
        self._lock = threading.RLock()
        # Ensure the data directory and file exist
        self._path.parent.mkdir(parents=True, exist_ok=True)
        if not self._path.exists():
            self._write_data({"users": []})

    # ------------------------------------------------------------------
    # Internal I/O helpers (caller holds the lock)
    # ------------------------------------------------------------------

    def _read_data(self) -> dict[str, Any]:
        """Read and parse the JSON file. Returns {"users": [...]}."""
        try:
            with open(self._path, "r", encoding="utf-8") as fh:
                return json.load(fh)
        except (FileNotFoundError, json.JSONDecodeError):
            return {"users": []}

    def _write_data(self, data: dict[str, Any]) -> None:
        """Write *data* atomically via a temporary file in the same directory."""
        dir_ = self._path.parent
        fd, tmp_path = tempfile.mkstemp(dir=dir_, suffix=".tmp")
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as fh:
                json.dump(data, fh, ensure_ascii=False)
            os.replace(tmp_path, self._path)
        except Exception:
            # Ensure the temp file is cleaned up on failure without replacing
            try:
                os.unlink(tmp_path)
            except OSError:
                pass
            raise

    def _find_by_email(
        self, users: list[dict[str, Any]], email: str
    ) -> dict[str, Any] | None:
        norm = email.lower()
        for u in users:
            if u["email"] == norm:
                return u
        return None

    # ------------------------------------------------------------------
    # UserRepository interface
    # ------------------------------------------------------------------

    def create(self, user: dict[str, Any]) -> dict[str, Any]:
        """REQ-USR-B01: atomically check and insert under the lock."""
        with self._lock:
            data = self._read_data()
            users = data["users"]
            if self._find_by_email(users, user["email"]) is not None:
                raise EmailAlreadyExists(user["email"])
            record = copy.deepcopy(user)
            users.append(record)
            self._write_data(data)
            return copy.deepcopy(record)

    def get(self, user_id: str) -> dict[str, Any] | None:
        with self._lock:
            data = self._read_data()
            for u in data["users"]:
                if u["id"] == user_id:
                    return copy.deepcopy(u)
            return None

    def get_by_email(self, email: str) -> dict[str, Any] | None:
        with self._lock:
            data = self._read_data()
            record = self._find_by_email(data["users"], email)
            return copy.deepcopy(record) if record is not None else None

    def list(
        self,
        filters: dict[str, Any],
        page: int,
        page_size: int,
    ) -> tuple[list[dict[str, Any]], int]:
        """REQ-USR-03, REQ-USR-B03: sorted, filtered, paginated list."""
        with self._lock:
            data = self._read_data()
            records = data["users"]

        # Apply filters
        role_filter = filters.get("role")
        email_filter = filters.get("email")
        if role_filter is not None:
            records = [r for r in records if r["role"] == role_filter]
        if email_filter is not None:
            norm = email_filter.lower()
            records = [r for r in records if r["email"] == norm]

        # Stable sort: (created_at, id) ascending
        records = sorted(records, key=lambda r: (r["created_at"], r["id"]))

        total = len(records)
        offset = (page - 1) * page_size
        if offset >= total:
            return [], total
        page_records = records[offset : offset + page_size]
        return [copy.deepcopy(r) for r in page_records], total

    def update(self, user_id: str, user: dict[str, Any]) -> dict[str, Any] | None:
        """REQ-USR-B01: atomically check uniqueness (excluding own id)."""
        with self._lock:
            data = self._read_data()
            users = data["users"]
            idx = next((i for i, u in enumerate(users) if u["id"] == user_id), None)
            if idx is None:
                return None
            # Check email uniqueness against other users
            norm_email = user["email"].lower()
            for u in users:
                if u["id"] != user_id and u["email"] == norm_email:
                    raise EmailAlreadyExists(user["email"])
            updated = copy.deepcopy(user)
            users[idx] = updated
            self._write_data(data)
            return copy.deepcopy(updated)

    def delete(self, user_id: str) -> bool:
        with self._lock:
            data = self._read_data()
            users = data["users"]
            new_users = [u for u in users if u["id"] != user_id]
            if len(new_users) == len(users):
                return False
            data["users"] = new_users
            self._write_data(data)
            return True

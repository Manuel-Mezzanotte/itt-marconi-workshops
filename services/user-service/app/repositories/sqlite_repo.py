"""SQLite-based UserRepository implementation.

Data is stored in DATA_DIR/users.db. The table schema matches the eight User
fields exactly. Each operation opens and closes its own connection; connections
are never shared between threads or calls.

Uniqueness is enforced via a UNIQUE COLLATE NOCASE constraint on email AND by
catching the IntegrityError that SQLite raises. Writes use BEGIN IMMEDIATE /
COMMIT to prevent TOCTOU races.

REQ-USR-09.4, REQ-USR-09.7 (persistence across restarts)
REQ-USR-B01 (email uniqueness via UNIQUE constraint)
REQ-USR-12.3 (SQLite backend)
"""
from __future__ import annotations

import copy
import sqlite3
from pathlib import Path
from typing import Any

from app.errors import EmailAlreadyExists
from app.repositories import UserRepository

_FILENAME = "users.db"

_CREATE_TABLE = """
CREATE TABLE IF NOT EXISTS users (
    id          TEXT NOT NULL PRIMARY KEY,
    first_name  TEXT NOT NULL,
    last_name   TEXT NOT NULL,
    email       TEXT NOT NULL UNIQUE COLLATE NOCASE,
    company     TEXT,
    role        TEXT NOT NULL,
    created_at  TEXT NOT NULL,
    updated_at  TEXT NOT NULL
);
"""

_FIELDS = ("id", "first_name", "last_name", "email", "company", "role", "created_at", "updated_at")


def _row_to_dict(row: sqlite3.Row) -> dict[str, Any]:
    """Convert a sqlite3.Row to a plain dict."""
    return dict(row)


class SqliteRepository(UserRepository):
    """Persist User records in an SQLite database.

    Each public method opens a fresh connection with isolation_level=None
    (which disables implicit transactions — not autocommit), uses explicit
    BEGIN IMMEDIATE / COMMIT / ROLLBACK, and closes the connection before
    returning.
    """

    def __init__(self, data_dir: Path) -> None:
        self._db_path = Path(data_dir) / _FILENAME
        self._db_path.parent.mkdir(parents=True, exist_ok=True)
        # Initialise the schema
        conn = self._connect()
        try:
            conn.execute(_CREATE_TABLE)
            conn.commit()
        finally:
            conn.close()

    # ------------------------------------------------------------------
    # Connection helper
    # ------------------------------------------------------------------

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self._db_path), isolation_level=None)
        conn.row_factory = sqlite3.Row
        return conn

    # ------------------------------------------------------------------
    # UserRepository interface
    # ------------------------------------------------------------------

    def create(self, user: dict[str, Any]) -> dict[str, Any]:
        """REQ-USR-B01: INSERT fails atomically on duplicate email."""
        conn = self._connect()
        try:
            conn.execute("BEGIN IMMEDIATE")
            conn.execute(
                "INSERT INTO users (id, first_name, last_name, email, company, role, "
                "created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    user["id"],
                    user["first_name"],
                    user["last_name"],
                    user["email"],
                    user.get("company"),
                    user["role"],
                    user["created_at"],
                    user["updated_at"],
                ),
            )
            conn.commit()
            return copy.deepcopy(user)
        except sqlite3.IntegrityError:
            conn.rollback()
            raise EmailAlreadyExists(user["email"])
        finally:
            conn.close()

    def get(self, user_id: str) -> dict[str, Any] | None:
        conn = self._connect()
        try:
            row = conn.execute(
                "SELECT * FROM users WHERE id = ?", (user_id,)
            ).fetchone()
            return _row_to_dict(row) if row is not None else None
        finally:
            conn.close()

    def get_by_email(self, email: str) -> dict[str, Any] | None:
        conn = self._connect()
        try:
            row = conn.execute(
                "SELECT * FROM users WHERE email = ? COLLATE NOCASE", (email,)
            ).fetchone()
            return _row_to_dict(row) if row is not None else None
        finally:
            conn.close()

    def list(
        self,
        filters: dict[str, Any],
        page: int,
        page_size: int,
    ) -> tuple[list[dict[str, Any]], int]:
        """REQ-USR-03, REQ-USR-B03: sorted, filtered, paginated list."""
        conditions: list[str] = []
        params: list[Any] = []

        role_filter = filters.get("role")
        email_filter = filters.get("email")

        if role_filter is not None:
            conditions.append("role = ?")
            params.append(role_filter)
        if email_filter is not None:
            conditions.append("email = ? COLLATE NOCASE")
            params.append(email_filter.lower())

        where = ("WHERE " + " AND ".join(conditions)) if conditions else ""

        conn = self._connect()
        try:
            # Total count before pagination
            count_row = conn.execute(
                f"SELECT COUNT(*) FROM users {where}", params
            ).fetchone()
            total = count_row[0]

            if total == 0:
                return [], 0

            offset = (page - 1) * page_size
            # Guard against enormous offsets to avoid SQLite overflow
            if offset >= total:
                return [], total

            rows = conn.execute(
                f"SELECT * FROM users {where} ORDER BY created_at ASC, id ASC "
                f"LIMIT ? OFFSET ?",
                params + [page_size, offset],
            ).fetchall()
            return [_row_to_dict(r) for r in rows], total
        finally:
            conn.close()

    def update(self, user_id: str, user: dict[str, Any]) -> dict[str, Any] | None:
        """REQ-USR-B01: UPDATE fails atomically if email belongs to another user."""
        conn = self._connect()
        try:
            conn.execute("BEGIN IMMEDIATE")
            # Check the record exists
            row = conn.execute(
                "SELECT id FROM users WHERE id = ?", (user_id,)
            ).fetchone()
            if row is None:
                conn.rollback()
                return None
            try:
                conn.execute(
                    "UPDATE users SET first_name=?, last_name=?, email=?, company=?, "
                    "role=?, created_at=?, updated_at=? WHERE id=?",
                    (
                        user["first_name"],
                        user["last_name"],
                        user["email"],
                        user.get("company"),
                        user["role"],
                        user["created_at"],
                        user["updated_at"],
                        user_id,
                    ),
                )
                conn.commit()
                return copy.deepcopy(user)
            except sqlite3.IntegrityError:
                conn.rollback()
                raise EmailAlreadyExists(user["email"])
        finally:
            conn.close()

    def delete(self, user_id: str) -> bool:
        conn = self._connect()
        try:
            conn.execute("BEGIN IMMEDIATE")
            cursor = conn.execute("DELETE FROM users WHERE id = ?", (user_id,))
            conn.commit()
            return cursor.rowcount > 0
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

import sqlite3
from contextlib import contextmanager
from copy import deepcopy
from pathlib import Path

from app.repositories import change_status, check_slot


FIELDS = ("id", "user_id", "event_id", "amount", "status", "created_at", "updated_at")


class SqliteRepository:
    def __init__(self, data_dir):
        self._path = Path(data_dir) / "registrations.db"
        self._path.parent.mkdir(parents=True, exist_ok=True)
        with self._connection(write=True) as connection:
            connection.execute("""
                CREATE TABLE IF NOT EXISTS registrations (
                    id TEXT PRIMARY KEY NOT NULL, user_id TEXT NOT NULL, event_id TEXT NOT NULL,
                    amount REAL NOT NULL, status TEXT NOT NULL,
                    created_at TEXT NOT NULL, updated_at TEXT NOT NULL
                )
            """)
            connection.execute("""
                CREATE UNIQUE INDEX IF NOT EXISTS unique_confirmed_registration
                ON registrations(user_id, event_id) WHERE status = 'confirmed'
            """)
            connection.execute("""
                CREATE INDEX IF NOT EXISTS registration_event_status
                ON registrations(event_id, status)
            """)

    @contextmanager
    def _connection(self, write=False):
        connection = sqlite3.connect(self._path, isolation_level=None)
        connection.row_factory = sqlite3.Row
        try:
            if write:
                connection.execute("BEGIN IMMEDIATE")
            yield connection
            if write:
                connection.commit()
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()

    def reserve(self, record, capacity):
        with self._connection(write=True) as connection:
            duplicate = connection.execute(
                "SELECT 1 FROM registrations WHERE user_id=? AND event_id=? AND status='confirmed'",
                (record["user_id"], record["event_id"]),
            ).fetchone()
            count = connection.execute(
                "SELECT COUNT(*) FROM registrations WHERE event_id=? AND status='confirmed'",
                (record["event_id"],),
            ).fetchone()[0]
            check_slot(duplicate is not None, count, capacity)
            if connection.execute("SELECT 1 FROM registrations WHERE id=?", (record["id"],)).fetchone():
                raise ValueError("Duplicate registration id")
            connection.execute(
                "INSERT INTO registrations (id,user_id,event_id,amount,status,created_at,updated_at) "
                "VALUES (?,?,?,?,?,?,?)", tuple(record[field] for field in FIELDS),
            )
        return deepcopy(record)

    def get(self, registration_id):
        with self._connection() as connection:
            row = connection.execute("SELECT * FROM registrations WHERE id=?", (registration_id,)).fetchone()
            return dict(row) if row else None

    def list(self, filters, page, page_size):
        conditions, parameters = [], []
        for field in ("user_id", "event_id", "status"):
            if filters.get(field) is not None:
                conditions.append(f"{field}=?")
                parameters.append(filters[field])
        where = " WHERE " + " AND ".join(conditions) if conditions else ""
        with self._connection() as connection:
            connection.execute("BEGIN")
            total = connection.execute("SELECT COUNT(*) FROM registrations" + where, parameters).fetchone()[0]
            offset = (page - 1) * page_size
            if offset >= total:
                return [], total
            rows = connection.execute(
                "SELECT * FROM registrations" + where + " ORDER BY created_at,id LIMIT ? OFFSET ?",
                parameters + [page_size, offset],
            ).fetchall()
            return [dict(row) for row in rows], total

    def count_confirmed(self, event_id):
        with self._connection() as connection:
            return connection.execute(
                "SELECT COUNT(*) FROM registrations WHERE event_id=? AND status='confirmed'", (event_id,),
            ).fetchone()[0]

    def update_status(self, registration_id, status, updated_at):
        with self._connection(write=True) as connection:
            row = connection.execute("SELECT * FROM registrations WHERE id=?", (registration_id,)).fetchone()
            if row is None:
                return None
            current = dict(row)
            updated = change_status(current, status, updated_at)
            if updated != current:
                connection.execute("UPDATE registrations SET status=?,updated_at=? WHERE id=?",
                                   (status, updated_at, registration_id))
            return updated

    def delete(self, registration_id):
        with self._connection(write=True) as connection:
            return connection.execute("DELETE FROM registrations WHERE id=?", (registration_id,)).rowcount > 0

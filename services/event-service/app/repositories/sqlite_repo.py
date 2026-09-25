import json
import sqlite3
from contextlib import contextmanager
from copy import deepcopy
from pathlib import Path

from app.repositories import paginate


class SqliteRepository:
    def __init__(self, data_dir):
        self._path = Path(data_dir) / "events.db"
        self._path.parent.mkdir(parents=True, exist_ok=True)
        with self._connection(write=True) as connection:
            connection.execute(
                "CREATE TABLE IF NOT EXISTS events (id TEXT PRIMARY KEY, document TEXT NOT NULL)"
            )

    @contextmanager
    def _connection(self, write=False):
        connection = sqlite3.connect(self._path, isolation_level=None)
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

    def create(self, record):
        with self._connection(write=True) as connection:
            try:
                connection.execute(
                    "INSERT INTO events (id, document) VALUES (?, ?)",
                    (record["id"], json.dumps(record, allow_nan=False)),
                )
            except sqlite3.IntegrityError as exc:
                raise ValueError("Duplicate event id") from exc
        return deepcopy(record)

    def get(self, event_id):
        with self._connection() as connection:
            row = connection.execute(
                "SELECT document FROM events WHERE id = ?", (event_id,),
            ).fetchone()
            return json.loads(row[0]) if row else None

    def list(self, filters, page, page_size):
        with self._connection() as connection:
            records = [json.loads(row[0]) for row in connection.execute("SELECT document FROM events")]
        return paginate(records, filters, page, page_size)

    def update(self, event_id, transform):
        with self._connection(write=True) as connection:
            row = connection.execute(
                "SELECT document FROM events WHERE id = ?", (event_id,),
            ).fetchone()
            if row is None:
                return None
            updated = transform(json.loads(row[0]))
            connection.execute(
                "UPDATE events SET document = ? WHERE id = ?",
                (json.dumps(updated, allow_nan=False), event_id),
            )
        return deepcopy(updated)

    def delete(self, event_id):
        with self._connection(write=True) as connection:
            deleted = connection.execute("DELETE FROM events WHERE id = ?", (event_id,))
            return deleted.rowcount > 0

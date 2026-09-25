import json
import os
import tempfile
from pathlib import Path

from app.repositories.memory import MemoryRepository


class JsonRepository(MemoryRepository):
    def __init__(self, data_dir):
        super().__init__()
        self._path = Path(data_dir) / "registrations.json"
        self._path.parent.mkdir(parents=True, exist_ok=True)

    def _read(self):
        if not self._path.exists():
            return {}
        data = json.loads(self._path.read_text(encoding="utf-8"))
        return {record["id"]: record for record in data["registrations"]}

    def _write(self, records):
        descriptor, filename = tempfile.mkstemp(dir=self._path.parent, suffix=".tmp")
        try:
            with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
                json.dump({"registrations": list(records.values())}, stream,
                          ensure_ascii=False, allow_nan=False)
            os.replace(filename, self._path)
        finally:
            Path(filename).unlink(missing_ok=True)

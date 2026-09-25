import os
from pathlib import Path
from urllib.parse import urlsplit


def load_config(overrides=None):
    values = {
        "PORT": os.getenv("PORT", "5002"),
        "USER_SERVICE_URL": os.getenv("USER_SERVICE_URL", "http://localhost:5001"),
        "STORAGE_BACKEND": os.getenv("STORAGE_BACKEND", "memory"),
        "DATA_DIR": os.getenv("DATA_DIR", "./data"),
    }
    values.update(overrides or {})
    raw_port = values["PORT"]
    if isinstance(raw_port, bool) or not isinstance(raw_port, (str, int)):
        raise ValueError("PORT must be an integer")
    port = int(raw_port)
    if not 1 <= port <= 65535:
        raise ValueError("PORT must be between 1 and 65535")
    backend = str(values["STORAGE_BACKEND"]).lower()
    if backend not in {"memory", "json", "sqlite"}:
        raise ValueError("Unknown STORAGE_BACKEND")
    url = values["USER_SERVICE_URL"]
    if not isinstance(url, str):
        raise ValueError("USER_SERVICE_URL must be an HTTP URL")
    parsed = urlsplit(url)
    if (parsed.scheme not in {"http", "https"} or not parsed.hostname
            or parsed.query or parsed.fragment or parsed.username or parsed.password):
        raise ValueError("Invalid USER_SERVICE_URL")
    parsed.port
    return {
        "PORT": port, "STORAGE_BACKEND": backend,
        "DATA_DIR": Path(values["DATA_DIR"]), "USER_SERVICE_URL": url.rstrip("/"),
    }

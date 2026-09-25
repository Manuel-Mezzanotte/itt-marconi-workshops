"""Configuration loader for user-service.

Single point of environment reading: PORT, STORAGE_BACKEND, DATA_DIR.
Call load_config() at application factory time; never read os.environ elsewhere.
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import Any

_VALID_BACKENDS = {"memory", "json", "sqlite"}


def load_config(overrides: dict[str, Any] | None = None) -> dict[str, Any]:
    """Read configuration from the environment and apply optional overrides.

    Parameters
    ----------
    overrides:
        Dict of key→value pairs that take precedence over the environment.
        Useful for tests. Values are applied *before* type coercion so that
        the same validation rules are always exercised.

    Returns
    -------
    dict with keys PORT (int), STORAGE_BACKEND (str), DATA_DIR (Path).

    Raises
    ------
    ValueError
        If PORT is not a valid integer in [1, 65535] or STORAGE_BACKEND is
        not one of memory / json / sqlite.
    """
    raw: dict[str, Any] = {
        "PORT": os.environ.get("PORT", "5001"),
        "STORAGE_BACKEND": os.environ.get("STORAGE_BACKEND", "memory"),
        "DATA_DIR": os.environ.get("DATA_DIR", "./data"),
    }
    if overrides:
        raw.update(overrides)

    # --- PORT ---
    try:
        port = int(raw["PORT"])
    except (ValueError, TypeError) as exc:
        raise ValueError(
            f"PORT must be an integer, got: {raw['PORT']!r}"
        ) from exc
    if not (1 <= port <= 65535):
        raise ValueError(
            f"PORT must be between 1 and 65535, got: {port}"
        )

    # --- STORAGE_BACKEND ---
    backend = str(raw["STORAGE_BACKEND"]).lower()
    if backend not in _VALID_BACKENDS:
        raise ValueError(
            f"STORAGE_BACKEND must be one of {sorted(_VALID_BACKENDS)}, "
            f"got: {raw['STORAGE_BACKEND']!r}"
        )

    # --- DATA_DIR ---
    data_dir = Path(raw["DATA_DIR"])

    return {
        "PORT": port,
        "STORAGE_BACKEND": backend,
        "DATA_DIR": data_dir,
    }

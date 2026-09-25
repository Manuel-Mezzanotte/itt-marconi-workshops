"""Tests for app/config.py — REQ-USR-09."""
from pathlib import Path

import pytest

from app.config import load_config


@pytest.fixture(autouse=True)
def isolated_configuration_environment(monkeypatch):
    for name in ("PORT", "STORAGE_BACKEND", "DATA_DIR"):
        monkeypatch.delenv(name, raising=False)


def test_environment_configuration_and_override_precedence(monkeypatch, tmp_path):
    """REQ-USR-09: read environment at call time; explicit overrides take precedence."""
    monkeypatch.setenv("PORT", "15501")
    monkeypatch.setenv("STORAGE_BACKEND", "sqlite")
    monkeypatch.setenv("DATA_DIR", str(tmp_path))
    assert load_config() == {"PORT": 15501, "STORAGE_BACKEND": "sqlite", "DATA_DIR": tmp_path}
    assert load_config({"PORT": 6001, "STORAGE_BACKEND": "memory"}) == {
        "PORT": 6001, "STORAGE_BACKEND": "memory", "DATA_DIR": tmp_path,
    }


# ---------------------------------------------------------------------------
# Default values
# ---------------------------------------------------------------------------


def test_defaults():
    """REQ-USR-09: default PORT=5001, STORAGE_BACKEND=memory, DATA_DIR=Path('./data')."""
    cfg = load_config()
    assert cfg["PORT"] == 5001
    assert cfg["STORAGE_BACKEND"] == "memory"
    assert cfg["DATA_DIR"] == Path("./data")
    assert isinstance(cfg["DATA_DIR"], Path)


# ---------------------------------------------------------------------------
# Override values
# ---------------------------------------------------------------------------


def test_override_port():
    """REQ-USR-09: PORT can be overridden to an integer."""
    cfg = load_config({"PORT": 8080})
    assert cfg["PORT"] == 8080


def test_override_port_as_string():
    """REQ-USR-09: PORT supplied as string is converted to int."""
    cfg = load_config({"PORT": "9000"})
    assert cfg["PORT"] == 9000


def test_override_backend_json():
    """REQ-USR-09: STORAGE_BACKEND can be overridden to json."""
    cfg = load_config({"STORAGE_BACKEND": "json"})
    assert cfg["STORAGE_BACKEND"] == "json"


def test_override_backend_sqlite():
    """REQ-USR-09: STORAGE_BACKEND can be overridden to sqlite."""
    cfg = load_config({"STORAGE_BACKEND": "sqlite"})
    assert cfg["STORAGE_BACKEND"] == "sqlite"


def test_override_data_dir():
    """REQ-USR-09: DATA_DIR override is converted to Path."""
    cfg = load_config({"DATA_DIR": "/tmp/mydata"})
    assert cfg["DATA_DIR"] == Path("/tmp/mydata")
    assert isinstance(cfg["DATA_DIR"], Path)


def test_override_multiple():
    """REQ-USR-09: multiple overrides are all applied."""
    cfg = load_config({"PORT": 7000, "STORAGE_BACKEND": "sqlite", "DATA_DIR": "/tmp/x"})
    assert cfg["PORT"] == 7000
    assert cfg["STORAGE_BACKEND"] == "sqlite"
    assert cfg["DATA_DIR"] == Path("/tmp/x")


# ---------------------------------------------------------------------------
# Validation errors
# ---------------------------------------------------------------------------


def test_invalid_port_string():
    """REQ-USR-09: non-integer PORT raises ValueError."""
    with pytest.raises((ValueError, TypeError)):
        load_config({"PORT": "not-a-number"})


def test_invalid_port_zero():
    """REQ-USR-09: PORT=0 is out of range → ValueError."""
    with pytest.raises(ValueError):
        load_config({"PORT": 0})


def test_invalid_port_too_large():
    """REQ-USR-09: PORT > 65535 → ValueError."""
    with pytest.raises(ValueError):
        load_config({"PORT": 99999})


def test_invalid_backend():
    """REQ-USR-09: unknown STORAGE_BACKEND raises ValueError."""
    with pytest.raises(ValueError):
        load_config({"STORAGE_BACKEND": "redis"})


def test_invalid_backend_empty():
    """REQ-USR-09: empty STORAGE_BACKEND raises ValueError."""
    with pytest.raises(ValueError):
        load_config({"STORAGE_BACKEND": ""})

"""REQ-EVT-04, REQ-EVT-05, REQ-EVT-06."""
import runpy
import socket
from unittest.mock import patch

import pytest
from flask import abort

from app import create_app
from app.config import load_config
from app.errors import ApiError


pytestmark = pytest.mark.req("REQ-EVT-05")


def test_config_defaults_environment_and_override(monkeypatch, tmp_path):
    for key in ("PORT", "DATA_DIR", "STORAGE_BACKEND", "USER_SERVICE_URL"):
        monkeypatch.delenv(key, raising=False)
    assert load_config()["PORT"] == 5002
    assert load_config()["USER_SERVICE_URL"] == "http://localhost:5001"
    monkeypatch.setenv("PORT", "15402")
    monkeypatch.setenv("STORAGE_BACKEND", "json")
    monkeypatch.setenv("DATA_DIR", str(tmp_path))
    monkeypatch.setenv("USER_SERVICE_URL", "https://users.test/base/")
    config = load_config()
    assert config == {
        "PORT": 15402, "STORAGE_BACKEND": "json", "DATA_DIR": tmp_path,
        "USER_SERVICE_URL": "https://users.test/base",
    }
    assert load_config({"PORT": 6002})["PORT"] == 6002


@pytest.mark.parametrize("overrides", [
    {"PORT": 0}, {"PORT": 65536}, {"PORT": "bad"}, {"PORT": 1.5}, {"PORT": True},
    {"STORAGE_BACKEND": "postgres"}, {"USER_SERVICE_URL": None},
    {"USER_SERVICE_URL": "ftp://users.test"}, {"USER_SERVICE_URL": "http://"},
    {"USER_SERVICE_URL": "http://user:password@users.test"},
    {"USER_SERVICE_URL": "http://users.test/?query=value"},
    {"USER_SERVICE_URL": "http://users.test/#fragment"},
    {"USER_SERVICE_URL": "http://users.test:invalid"},
])
def test_invalid_configuration(overrides):
    with pytest.raises(ValueError):
        load_config(overrides)


@pytest.mark.req("REQ-EVT-04")
def test_health_without_dependency(api, contract):
    assert contract(api.get("/health"), "GET", "/health") == {
        "status": "ok", "service": "event-service",
    }


@pytest.mark.parametrize("method,path,status,code", [
    ("GET", "/missing", 404, "NOT_FOUND"),
    ("POST", "/health", 405, "METHOD_NOT_ALLOWED"),
])
@pytest.mark.req("REQ-EVT-04")
def test_uniform_http_errors(api, method, path, status, code):
    response = api.open(path, method=method)
    assert response.status_code == status
    assert response.get_json()["error"]["code"] == code


@pytest.mark.req("REQ-EVT-04")
def test_domain_and_other_http_errors():
    application = create_app({"STORAGE_BACKEND": "memory"})

    @application.get("/domain")
    def domain():
        raise ApiError(422, "VALIDATION_ERROR", "Invalid value", {"field": "title"})

    @application.get("/http")
    def http():
        abort(403)

    client = application.test_client()
    assert client.get("/domain").get_json() == {
        "error": {"code": "VALIDATION_ERROR", "message": "Invalid value",
                  "details": {"field": "title"}},
    }
    assert client.get("/http").status_code == 403
    assert client.get("/http").get_json()["error"]["code"] == "HTTP_ERROR"


def test_factories_are_independent():
    first = create_app({"PORT": 5002, "STORAGE_BACKEND": "memory"})
    second = create_app({"PORT": 6002, "STORAGE_BACKEND": "memory"})
    assert first is not second
    assert first.config["EVENT_SERVICE_CONFIG"]["PORT"] == 5002
    assert second.config["EVENT_SERVICE_CONFIG"]["PORT"] == 6002


def test_startup_without_reverse_dns_or_reloader(monkeypatch):
    with socket.socket() as probe:
        probe.bind(("127.0.0.1", 0))
        port = probe.getsockname()[1]
    monkeypatch.setenv("PORT", str(port))
    monkeypatch.setenv("STORAGE_BACKEND", "memory")
    monkeypatch.setenv("FLASK_DEBUG", "1")
    observed = []

    def serve(server):
        assert server.server_address == ("127.0.0.1", port)
        assert server.app.debug is False
        observed.append(server.app.test_client().get("/health").status_code)

    with patch("socket.getfqdn", side_effect=RuntimeError("DNS unavailable")), \
         patch("werkzeug.serving.BaseWSGIServer.serve_forever", serve), \
         patch("werkzeug._reloader.run_with_reloader", side_effect=AssertionError("reloader")):
        runpy.run_module("app.__main__", run_name="__main__")
    assert observed == [200]
    with socket.socket() as probe:
        assert probe.connect_ex(("127.0.0.1", port)) != 0

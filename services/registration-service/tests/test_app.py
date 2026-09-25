"""REQ-REG-04, REQ-REG-05: configuration, errors and startup."""
import runpy
import socket
from unittest.mock import patch

import pytest
from flask import abort

from app import create_app
from app.config import load_config
from app.errors import ApiError


pytestmark = pytest.mark.req("REQ-REG-04")


def test_configuration_defaults_environment_overrides(monkeypatch, tmp_path):
    for key in ("PORT", "DATA_DIR", "STORAGE_BACKEND", "USER_SERVICE_URL", "EVENT_SERVICE_URL"):
        monkeypatch.delenv(key, raising=False)
    config = load_config()
    assert config["PORT"] == 5003
    assert config["USER_SERVICE_URL"] == "http://localhost:5001"
    assert config["EVENT_SERVICE_URL"] == "http://localhost:5002"
    monkeypatch.setenv("PORT", "15503")
    monkeypatch.setenv("STORAGE_BACKEND", "json")
    monkeypatch.setenv("DATA_DIR", str(tmp_path))
    monkeypatch.setenv("USER_SERVICE_URL", "http://users.test/")
    monkeypatch.setenv("EVENT_SERVICE_URL", "https://events.test/base/")
    assert load_config() == {
        "PORT": 15503, "STORAGE_BACKEND": "json", "DATA_DIR": tmp_path,
        "USER_SERVICE_URL": "http://users.test", "EVENT_SERVICE_URL": "https://events.test/base",
    }
    assert load_config({"PORT": 6003})["PORT"] == 6003


@pytest.mark.parametrize("config", [
    {"PORT": 0}, {"PORT": 65536}, {"PORT": "bad"}, {"PORT": True}, {"PORT": 1.5},
    {"STORAGE_BACKEND": "postgres"},
])
def test_invalid_configuration(config):
    with pytest.raises(ValueError):
        load_config(config)


@pytest.mark.parametrize("key", ["USER_SERVICE_URL", "EVENT_SERVICE_URL"])
@pytest.mark.parametrize("value", [None, "ftp://host", "http://", "http://user:secret@host",
                                  "http://host?query=x", "http://host#fragment", "http://host:bad"])
def test_invalid_dependency_url(key, value):
    with pytest.raises(ValueError):
        load_config({key: value})


def test_health_without_dependencies(api, contract):
    assert contract(api.get("/health"), "GET", "/health") == {
        "status": "ok", "service": "registration-service",
    }


@pytest.mark.parametrize("method,path,status,code", [
    ("GET", "/missing", 404, "NOT_FOUND"), ("POST", "/health", 405, "METHOD_NOT_ALLOWED"),
])
def test_http_errors(api, method, path, status, code):
    response = api.open(path, method=method)
    assert response.status_code == status
    assert response.get_json()["error"]["code"] == code


def test_domain_errors_and_app_isolation():
    application = create_app({"PORT": 5003, "STORAGE_BACKEND": "memory"})
    other = create_app({"PORT": 6003, "STORAGE_BACKEND": "memory"})
    assert application is not other
    assert application.config["REGISTRATION_SERVICE_CONFIG"]["PORT"] == 5003
    assert other.config["REGISTRATION_SERVICE_CONFIG"]["PORT"] == 6003

    @application.get("/domain")
    def domain():
        raise ApiError(422, "VALIDATION_ERROR", "Invalid", {"field": "user_id"})

    @application.get("/forbidden")
    def forbidden():
        abort(403)

    client = application.test_client()
    assert client.get("/domain").get_json() == {
        "error": {"code": "VALIDATION_ERROR", "message": "Invalid", "details": {"field": "user_id"}},
    }
    assert client.get("/forbidden").get_json()["error"]["code"] == "HTTP_ERROR"


def test_startup_uses_port_without_debugger_or_reverse_dns(monkeypatch):
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

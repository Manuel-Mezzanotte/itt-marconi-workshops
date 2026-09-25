"""Tests for app factory, health endpoint and error handling.

REQ-USR-07 — health check
REQ-USR-08 — 404 / 405 uniform JSON errors
REQ-USR-09 — independent app instances, PORT driven startup
REQ-USR-12 — contract validation via assert_matches_contract
"""
from __future__ import annotations

import unittest.mock

import pytest

from app import create_app
from validator import assert_matches_contract


# ---------------------------------------------------------------------------
# Application factory independence
# ---------------------------------------------------------------------------


def test_two_apps_are_independent():
    """REQ-USR-09: two create_app() calls return distinct Flask instances."""
    app1 = create_app({"STORAGE_BACKEND": "memory"})
    app2 = create_app({"STORAGE_BACKEND": "memory"})
    assert app1 is not app2


def test_configs_are_independent():
    """REQ-USR-09: each app carries its own configuration."""
    app1 = create_app({"PORT": 5001, "STORAGE_BACKEND": "memory"})
    app2 = create_app({"PORT": 6001, "STORAGE_BACKEND": "memory"})
    cfg1 = app1.config["USER_SERVICE_CONFIG"]
    cfg2 = app2.config["USER_SERVICE_CONFIG"]
    assert cfg1 is not cfg2
    assert cfg1["PORT"] == 5001
    assert cfg2["PORT"] == 6001


# ---------------------------------------------------------------------------
# Health endpoint — REQ-USR-07, REQ-USR-12
# ---------------------------------------------------------------------------


def test_health_status_200(client):
    """REQ-USR-07: GET /health returns 200."""
    resp = client.get("/health")
    assert resp.status_code == 200


def test_health_body(client):
    """REQ-USR-07: GET /health body is {"status":"ok","service":"user-service"}."""
    resp = client.get("/health")
    data = resp.get_json()
    assert data == {"status": "ok", "service": "user-service"}


def test_health_matches_contract(client):
    """REQ-USR-07, REQ-USR-12: GET /health passes contract validation."""
    resp = client.get("/health")
    assert_matches_contract(
        "user-service",
        "GET",
        "/health",
        {
            "status_code": resp.status_code,
            "headers": dict(resp.headers),
            "json": resp.get_json(),
        },
    )


# ---------------------------------------------------------------------------
# 404 for unknown paths — REQ-USR-08
# ---------------------------------------------------------------------------


def test_unknown_path_returns_404(client):
    """REQ-USR-08: GET on an undefined path returns 404."""
    resp = client.get("/api/v1/unknown-path")
    assert resp.status_code == 404


def test_unknown_path_error_code(client):
    """REQ-USR-08: unknown path error body has code NOT_FOUND."""
    resp = client.get("/api/v1/unknown-path")
    data = resp.get_json()
    assert data["error"]["code"] == "NOT_FOUND"


def test_unknown_path_error_format(client):
    """REQ-USR-08: unknown path response follows uniform error envelope."""
    resp = client.get("/api/v1/unknown-path")
    data = resp.get_json()
    assert "error" in data
    assert "code" in data["error"]
    assert "message" in data["error"]


# ---------------------------------------------------------------------------
# 405 for unsupported method — REQ-USR-08
# ---------------------------------------------------------------------------


def test_method_not_allowed_returns_405(client):
    """REQ-USR-08: POST on /health (GET-only) returns 405."""
    resp = client.post("/health")
    assert resp.status_code == 405


def test_method_not_allowed_error_code(client):
    """REQ-USR-08: 405 body has code METHOD_NOT_ALLOWED."""
    resp = client.post("/health")
    data = resp.get_json()
    assert data["error"]["code"] == "METHOD_NOT_ALLOWED"


def test_method_not_allowed_error_format(client):
    """REQ-USR-08: 405 response follows uniform error envelope."""
    resp = client.post("/health")
    data = resp.get_json()
    assert "error" in data
    assert "code" in data["error"]
    assert "message" in data["error"]


# ---------------------------------------------------------------------------
# __main__ entrypoint — REQ-USR-09
# ---------------------------------------------------------------------------


def test_main_calls_run_with_correct_args():
    """REQ-USR-09: __main__ calls app.run(host='127.0.0.1', port=5001) without debug or reloader."""
    import runpy

    with unittest.mock.patch("flask.Flask.run") as mock_run:
        runpy.run_module("app.__main__", run_name="__main__", alter_sys=False)

    mock_run.assert_called_once()
    call_args = mock_run.call_args
    # Accept positional or keyword arguments
    all_args = {}
    if call_args.args:
        all_args["host"] = call_args.args[0] if len(call_args.args) > 0 else None
        all_args["port"] = call_args.args[1] if len(call_args.args) > 1 else None
    all_args.update(call_args.kwargs)

    assert all_args.get("host") == "127.0.0.1"
    assert all_args.get("port") == 5001
    assert not all_args.get("debug", False)
    assert not all_args.get("use_reloader", False)


def test_main_ignores_flask_debug_env(monkeypatch):
    """REQ-USR-09: FLASK_DEBUG=1 must not enable debugger or reloader (issue #2).

    Intercepts werkzeug.serving.run_simple — the real server entry point used
    by Flask.run() — so that Flask's internal flag propagation is fully visible.
    """
    import os
    import runpy

    monkeypatch.setenv("FLASK_DEBUG", "1")
    monkeypatch.setenv("PORT", "15551")

    with unittest.mock.patch("werkzeug.serving.run_simple") as mock_server, \
         unittest.mock.patch("flask.cli.show_server_banner"):
        runpy.run_module("app.__main__", run_name="__main__", alter_sys=False)

    mock_server.assert_called_once()
    call_args = mock_server.call_args

    # Collect all keyword args (werkzeug.serving.run_simple uses keyword args)
    kwargs = call_args.kwargs if call_args.kwargs else {}
    # Also handle positional: run_simple(hostname, port, application, ...)
    # use_reloader and use_debugger are always keyword args in werkzeug
    assert kwargs.get("use_reloader") is False, (
        f"use_reloader must be False when FLASK_DEBUG=1, got: {kwargs.get('use_reloader')}"
    )
    assert kwargs.get("use_debugger") is False, (
        f"use_debugger must be False when FLASK_DEBUG=1, got: {kwargs.get('use_debugger')}"
    )
    # Verify port is taken from PORT env var
    positional = call_args.args if call_args.args else ()
    port_value = positional[1] if len(positional) > 1 else kwargs.get("port")
    assert port_value == 15551, f"Expected port 15551, got: {port_value}"

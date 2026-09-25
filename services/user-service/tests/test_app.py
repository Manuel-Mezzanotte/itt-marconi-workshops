"""Tests for app factory, health endpoint and error handling.

REQ-USR-07 — health check
REQ-USR-08 — 404 / 405 uniform JSON errors
REQ-USR-09 — independent app instances, PORT driven startup
REQ-USR-12 — contract validation via assert_matches_contract
"""
from __future__ import annotations

from unittest.mock import Mock, patch

import pytest

from app import create_app
from app.repositories import UserRepository
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


@pytest.mark.req("REQ-USR-08")
def test_internal_storage_error_returns_uniform_json_without_details():
    """Platform Standards §4: an unexpected storage failure must remain a JSON error (issue #8)."""
    repository = Mock(spec=UserRepository)
    repository.create.side_effect = OSError("private disk path and diagnostic")
    with patch("app.get_repository", return_value=repository):
        application = create_app({"STORAGE_BACKEND": "memory"})
    response = application.test_client().post("/api/v1/users", json={
        "first_name": "Ada", "last_name": "Lovelace", "email": "ada@example.com",
    })
    assert response.status_code == 500
    assert response.mimetype == "application/json"
    assert response.get_json() == {
        "error": {"code": "INTERNAL_ERROR", "message": "Internal server error", "details": {}},
    }
    assert "private disk" not in response.get_data(as_text=True)

"""POST /api/v1/users route tests [T-03].

REQ-USR-01, REQ-USR-B01, REQ-USR-B02, REQ-USR-10, REQ-USR-12
"""
from __future__ import annotations

import json
from pathlib import Path
from uuid import UUID

import pytest

from app import create_app
from app.repositories import get_repository
from app.service import UserService
from validator import assert_matches_contract


@pytest.fixture(params=["memory", "json", "sqlite"])
def client_with_backend(request, tmp_path):
    """Flask test client for each backend."""
    backend = request.param
    app = create_app({
        "STORAGE_BACKEND": backend,
        "DATA_DIR": str(tmp_path / backend),
        "PORT": 5001,
    })
    app.config["TESTING"] = True
    return app.test_client(), backend


class TestPostUsersCreate:
    """POST /api/v1/users endpoint [T-03]."""

    def test_post_success_201(self, client_with_backend):
        """POST with valid payload returns 201."""
        client, _ = client_with_backend
        payload = {
            "first_name": "Alice",
            "last_name": "Smith",
            "email": "alice@example.com",
        }
        resp = client.post("/api/v1/users", json=payload)
        assert resp.status_code == 201

    def test_post_success_location_header(self, client_with_backend):
        """POST returns Location header with created resource URL."""
        client, _ = client_with_backend
        payload = {
            "first_name": "Alice",
            "last_name": "Smith",
            "email": "alice@example.com",
        }
        resp = client.post("/api/v1/users", json=payload)
        assert "Location" in resp.headers
        location = resp.headers["Location"]
        # Location should be relative /api/v1/users/{id}
        assert location.startswith("/api/v1/users/")
        assert not location.startswith("http")

    def test_post_success_body_contains_id(self, client_with_backend):
        """POST response body contains a valid UUID id."""
        client, _ = client_with_backend
        payload = {
            "first_name": "Alice",
            "last_name": "Smith",
            "email": "alice@example.com",
        }
        resp = client.post("/api/v1/users", json=payload)
        data = resp.get_json()
        assert "id" in data
        try:
            UUID(data["id"])
        except ValueError:
            pytest.fail("Returned id is not a valid UUID")

    def test_post_success_body_contains_timestamps(self, client_with_backend):
        """POST response body contains created_at and updated_at."""
        client, _ = client_with_backend
        payload = {
            "first_name": "Alice",
            "last_name": "Smith",
            "email": "alice@example.com",
        }
        resp = client.post("/api/v1/users", json=payload)
        data = resp.get_json()
        assert "created_at" in data
        assert "updated_at" in data
        assert data["created_at"] == data["updated_at"]
        assert data["created_at"].endswith("Z")

    def test_post_success_matches_contract(self, client_with_backend):
        """POST 201 response matches OpenAPI contract."""
        client, _ = client_with_backend
        payload = {
            "first_name": "Alice",
            "last_name": "Smith",
            "email": "alice@example.com",
        }
        resp = client.post("/api/v1/users", json=payload)
        assert_matches_contract(
            "user-service",
            "POST",
            "/api/v1/users",
            {
                "status_code": resp.status_code,
                "headers": dict(resp.headers),
                "json": resp.get_json(),
            },
        )

    def test_post_malformed_json_400(self, client_with_backend):
        """Malformed JSON returns 400."""
        client, _ = client_with_backend
        resp = client.post(
            "/api/v1/users",
            data="{invalid json",
            content_type="application/json",
        )
        assert resp.status_code == 400

    def test_post_malformed_json_error_code(self, client_with_backend):
        """Malformed JSON error has code MALFORMED_JSON."""
        client, _ = client_with_backend
        resp = client.post(
            "/api/v1/users",
            data="{invalid json",
            content_type="application/json",
        )
        data = resp.get_json()
        assert data["error"]["code"] == "MALFORMED_JSON"

    def test_post_json_null_422(self, client_with_backend):
        """JSON literal null returns 422 (valid JSON, invalid for POST)."""
        client, _ = client_with_backend
        resp = client.post(
            "/api/v1/users",
            data="null",
            content_type="application/json",
        )
        assert resp.status_code == 422

    def test_post_json_null_error_code(self, client_with_backend):
        """JSON null error has code VALIDATION_ERROR."""
        client, _ = client_with_backend
        resp = client.post(
            "/api/v1/users",
            data="null",
            content_type="application/json",
        )
        data = resp.get_json()
        assert data["error"]["code"] == "VALIDATION_ERROR"

    def test_post_json_array_422(self, client_with_backend):
        """JSON array returns 422."""
        client, _ = client_with_backend
        resp = client.post(
            "/api/v1/users",
            data="[1, 2, 3]",
            content_type="application/json",
        )
        assert resp.status_code == 422

    def test_post_json_string_422(self, client_with_backend):
        """JSON string returns 422."""
        client, _ = client_with_backend
        resp = client.post(
            "/api/v1/users",
            data='"just a string"',
            content_type="application/json",
        )
        assert resp.status_code == 422

    def test_post_json_number_422(self, client_with_backend):
        """JSON number returns 422."""
        client, _ = client_with_backend
        resp = client.post(
            "/api/v1/users",
            data="42",
            content_type="application/json",
        )
        assert resp.status_code == 422

    def test_post_extra_fields_422(self, client_with_backend):
        """Extra fields in payload return 422."""
        client, _ = client_with_backend
        payload = {
            "first_name": "Alice",
            "last_name": "Smith",
            "email": "alice@example.com",
            "extra_field": "not-allowed",
        }
        resp = client.post("/api/v1/users", json=payload)
        assert resp.status_code == 422

    def test_post_missing_required_field_422(self, client_with_backend):
        """Missing required field returns 422."""
        client, _ = client_with_backend
        payload = {
            "first_name": "Alice",
            # Missing last_name and email
        }
        resp = client.post("/api/v1/users", json=payload)
        assert resp.status_code == 422

    @pytest.mark.parametrize("readonly_field", ["id", "created_at", "updated_at"])
    def test_post_readonly_field_422_no_create(self, client_with_backend, readonly_field):
        """Issue #1: Read-only field in body returns 422 without creating user."""
        client, backend = client_with_backend
        payload = {
            "first_name": "Alice",
            "last_name": "Smith",
            "email": "alice@example.com",
            readonly_field: "should-be-rejected",
        }
        resp = client.post("/api/v1/users", json=payload)
        assert resp.status_code == 422
        data = resp.get_json()
        assert data["error"]["code"] == "VALIDATION_ERROR"
        assert "details" in data["error"]

        # Verify no user was created: send valid payload with same email, expect 201
        payload_valid = {
            "first_name": "Alice",
            "last_name": "Smith",
            "email": "alice@example.com",
        }
        resp_valid = client.post("/api/v1/users", json=payload_valid)
        assert resp_valid.status_code == 201

    def test_post_duplicate_email_409(self, client_with_backend):
        """Duplicate email returns 409."""
        client, _ = client_with_backend
        payload1 = {
            "first_name": "Alice",
            "last_name": "Smith",
            "email": "alice@example.com",
        }
        client.post("/api/v1/users", json=payload1)

        payload2 = {
            "first_name": "Bob",
            "last_name": "Jones",
            "email": "alice@example.com",
        }
        resp = client.post("/api/v1/users", json=payload2)
        assert resp.status_code == 409

    def test_post_duplicate_email_error_code(self, client_with_backend):
        """Duplicate email error has code EMAIL_ALREADY_EXISTS."""
        client, _ = client_with_backend
        payload1 = {
            "first_name": "Alice",
            "last_name": "Smith",
            "email": "alice@example.com",
        }
        client.post("/api/v1/users", json=payload1)

        payload2 = {
            "first_name": "Bob",
            "last_name": "Jones",
            "email": "alice@example.com",
        }
        resp = client.post("/api/v1/users", json=payload2)
        data = resp.get_json()
        assert data["error"]["code"] == "EMAIL_ALREADY_EXISTS"

    def test_post_email_case_insensitive_duplicate_409(self, client_with_backend):
        """Email duplicate check is case-insensitive."""
        client, _ = client_with_backend
        payload1 = {
            "first_name": "Alice",
            "last_name": "Smith",
            "email": "alice@example.com",
        }
        client.post("/api/v1/users", json=payload1)

        payload2 = {
            "first_name": "Bob",
            "last_name": "Jones",
            "email": "ALICE@EXAMPLE.COM",
        }
        resp = client.post("/api/v1/users", json=payload2)
        assert resp.status_code == 409

    def test_post_with_optional_fields(self, client_with_backend):
        """POST with company and role preserves them."""
        client, _ = client_with_backend
        payload = {
            "first_name": "Alice",
            "last_name": "Smith",
            "email": "alice@example.com",
            "company": "TechCorp",
            "role": "speaker",
        }
        resp = client.post("/api/v1/users", json=payload)
        assert resp.status_code == 201
        data = resp.get_json()
        assert data["company"] == "TechCorp"
        assert data["role"] == "speaker"

    def test_post_email_normalized_lowercase(self, client_with_backend):
        """Email in response is normalized to lowercase."""
        client, _ = client_with_backend
        payload = {
            "first_name": "Alice",
            "last_name": "Smith",
            "email": "Alice.Smith@EXAMPLE.COM",
        }
        resp = client.post("/api/v1/users", json=payload)
        data = resp.get_json()
        assert data["email"] == "alice.smith@example.com"

    def test_post_invalid_email_format_422(self, client_with_backend):
        """Invalid email format returns 422."""
        client, _ = client_with_backend
        payload = {
            "first_name": "Alice",
            "last_name": "Smith",
            "email": "not-a-valid-email",
        }
        resp = client.post("/api/v1/users", json=payload)
        assert resp.status_code == 422

    def test_post_wrong_type_field_422(self, client_with_backend):
        """Wrong field type returns 422."""
        client, _ = client_with_backend
        payload = {
            "first_name": 123,  # Should be string
            "last_name": "Smith",
            "email": "alice@example.com",
        }
        resp = client.post("/api/v1/users", json=payload)
        assert resp.status_code == 422

    def test_post_name_field_boundary_max(self, client_with_backend):
        """first_name/last_name at max length (50) is accepted."""
        client, _ = client_with_backend
        payload = {
            "first_name": "A" * 50,
            "last_name": "B" * 50,
            "email": "alice@example.com",
        }
        resp = client.post("/api/v1/users", json=payload)
        assert resp.status_code == 201

    def test_post_name_field_boundary_over_max(self, client_with_backend):
        """first_name/last_name over 50 chars returns 422."""
        client, _ = client_with_backend
        payload = {
            "first_name": "A" * 51,
            "last_name": "Smith",
            "email": "alice@example.com",
        }
        resp = client.post("/api/v1/users", json=payload)
        assert resp.status_code == 422

    def test_post_company_field_boundary_max(self, client_with_backend):
        """company at max length (100) is accepted."""
        client, _ = client_with_backend
        payload = {
            "first_name": "Alice",
            "last_name": "Smith",
            "email": "alice@example.com",
            "company": "C" * 100,
        }
        resp = client.post("/api/v1/users", json=payload)
        assert resp.status_code == 201

    def test_post_company_field_boundary_over_max(self, client_with_backend):
        """company over 100 chars returns 422."""
        client, _ = client_with_backend
        payload = {
            "first_name": "Alice",
            "last_name": "Smith",
            "email": "alice@example.com",
            "company": "C" * 101,
        }
        resp = client.post("/api/v1/users", json=payload)
        assert resp.status_code == 422

    def test_post_atomicity_on_validation_error(self, client_with_backend):
        """Validation error doesn't create partial record."""
        client, _ = client_with_backend
        payload = {
            "first_name": "A" * 51,  # Too long
            "last_name": "Smith",
            "email": "alice@example.com",
        }
        resp = client.post("/api/v1/users", json=payload)
        assert resp.status_code == 422

        # Verify nothing was created: send valid payload with same email, expect 201
        payload_valid = {
            "first_name": "Alice",
            "last_name": "Smith",
            "email": "alice@example.com",
        }
        resp_valid = client.post("/api/v1/users", json=payload_valid)
        assert resp_valid.status_code == 201

    def test_post_location_header_relative(self, client_with_backend):
        """Issue #4: Location header must be relative /api/v1/users/{id}, not absolute."""
        client, _ = client_with_backend
        payload = {
            "first_name": "Alice",
            "last_name": "Smith",
            "email": "alice@example.com",
        }
        resp = client.post("/api/v1/users", json=payload)
        assert resp.status_code == 201
        location = resp.headers.get("Location")
        assert location is not None
        assert location.startswith("/api/v1/users/")
        assert not location.startswith("http")

    def test_post_wrong_content_type_400_json(self, client_with_backend):
        """Issue #4: text/plain body must return 400 with JSON error, not 415 HTML."""
        client, _ = client_with_backend
        resp = client.post(
            "/api/v1/users",
            data="{}",
            content_type="text/plain",
        )
        assert resp.status_code == 400
        # Must be JSON, not HTML
        assert resp.content_type.startswith("application/json")
        data = resp.get_json()
        assert data["error"]["code"] == "MALFORMED_JSON"

    def test_post_wrong_content_type_no_create_then_valid(self, client_with_backend):
        """Issue #4: Invalid Content-Type doesn't create user; valid email can then be used."""
        client, _ = client_with_backend
        email = "alice@example.com"

        # First attempt with wrong Content-Type
        resp_invalid = client.post(
            "/api/v1/users",
            data="{}",
            content_type="text/plain",
        )
        assert resp_invalid.status_code == 400

        # Send valid payload with same email - should succeed (user was not created)
        payload = {
            "first_name": "Alice",
            "last_name": "Smith",
            "email": email,
        }
        resp_valid = client.post("/api/v1/users", json=payload)
        assert resp_valid.status_code == 201

    @pytest.mark.parametrize("invalid_role", [[], {}])
    def test_post_role_invalid_type_422(self, client_with_backend, invalid_role):
        """Issue #3: role with wrong type (list/dict) returns 422, not TypeError."""
        client, _ = client_with_backend
        email = "alice@example.com"
        payload = {
            "first_name": "Alice",
            "last_name": "Smith",
            "email": email,
            "role": invalid_role,
        }
        resp = client.post("/api/v1/users", json=payload)
        assert resp.status_code == 422
        data = resp.get_json()
        assert data["error"]["code"] == "VALIDATION_ERROR"

    @pytest.mark.parametrize("invalid_role", [[], {}])
    def test_post_role_invalid_type_no_create_then_valid(self, client_with_backend, invalid_role):
        """Issue #3: Invalid role type doesn't create user; valid POST with same email succeeds."""
        client, _ = client_with_backend
        email = "alice@example.com"

        # First attempt with invalid role type
        payload_invalid = {
            "first_name": "Alice",
            "last_name": "Smith",
            "email": email,
            "role": invalid_role,
        }
        resp_invalid = client.post("/api/v1/users", json=payload_invalid)
        assert resp_invalid.status_code == 422

        # Send valid payload with same email - should succeed (user was not created)
        payload_valid = {
            "first_name": "Alice",
            "last_name": "Smith",
            "email": email,
        }
        resp_valid = client.post("/api/v1/users", json=payload_valid)
        assert resp_valid.status_code == 201

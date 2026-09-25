"""REQ-USR-04, REQ-USR-B01, REQ-USR-B02, REQ-USR-10, REQ-USR-11, REQ-USR-12."""
from datetime import datetime, timezone
from unittest.mock import patch
from uuid import uuid4

import pytest


pytestmark = pytest.mark.req("REQ-USR-04")
BASE = "/api/v1/users"
PAYLOAD = {"first_name": "Grace", "last_name": "Hopper", "email": "GRACE@EXAMPLE.COM"}


def test_put_replaces_fields_resets_defaults_and_refreshes_timestamp(api, create_user, contract):
    original = create_user(company="Old Co", role="organizer")
    path = f"{BASE}/{original['id']}"
    instant = datetime(2030, 1, 2, 3, 4, 5, 123456, tzinfo=timezone.utc)
    with patch("app.service.datetime") as clock:
        clock.now.return_value = instant
        result = contract(api.put(path, json=PAYLOAD), "PUT", path)
    assert result == {
        **PAYLOAD, "email": "grace@example.com", "role": "attendee", "company": None,
        "id": original["id"], "created_at": original["created_at"],
        "updated_at": "2030-01-02T03:04:05.123456Z",
    }
    assert api.get(path).get_json() == result
    assert api.get(BASE, query_string={"email": original["email"]}).get_json()["total"] == 0
    assert create_user(email=original["email"])["id"] != original["id"]


def test_put_accepts_own_email_and_optional_fields(api, create_user, contract):
    original = create_user()
    path = f"{BASE}/{original['id']}"
    payload = {**PAYLOAD, "email": original["email"].upper(),
               "company": "New Co", "role": "speaker"}
    result = contract(api.put(path, json=payload), "PUT", path)
    assert result["email"] == original["email"]
    assert result["company"] == "New Co" and result["role"] == "speaker"


def test_put_conflict_preserves_both_users(api, create_user, contract):
    original = create_user()
    other = create_user(email="other@example.com")
    path = f"{BASE}/{original['id']}"
    payload = {**PAYLOAD, "email": other["email"].upper()}
    body = contract(api.put(path, json=payload), "PUT", path, 409)
    assert body["error"]["code"] == "EMAIL_ALREADY_EXISTS"
    assert api.get(path).get_json() == original
    assert api.get(f"{BASE}/{other['id']}").get_json() == other


def test_put_missing_user(api, contract):
    path = f"{BASE}/{uuid4()}"
    assert contract(api.put(path, json=PAYLOAD), "PUT", path, 404)["error"]["code"] == "NOT_FOUND"


@pytest.mark.parametrize("field", ["first_name", "last_name", "email"])
def test_put_required_fields(api, create_user, contract, field):
    original = create_user()
    path = f"{BASE}/{original['id']}"
    payload = {key: value for key, value in PAYLOAD.items() if key != field}
    assert contract(api.put(path, json=payload), "PUT", path, 422)["error"]["code"] == "VALIDATION_ERROR"
    assert api.get(path).get_json() == original


@pytest.mark.parametrize("field,value", [
    ("id", "client-id"), ("created_at", "2030-01-01T00:00:00Z"),
    ("updated_at", "2030-01-01T00:00:00Z"), ("extra", "unsupported"),
    ("first_name", ""), ("first_name", 1), ("first_name", "a" * 51),
    ("last_name", None), ("last_name", "a" * 51),
    ("email", "invalid"), ("company", []), ("company", "a" * 101),
    ("role", []), ("role", {}), ("role", "admin"),
])
def test_put_invalid_fields_leave_record_unchanged(api, create_user, contract, field, value):
    original = create_user()
    path = f"{BASE}/{original['id']}"
    body = contract(api.put(path, json={**PAYLOAD, field: value}), "PUT", path, 422)
    assert body["error"]["code"] == "VALIDATION_ERROR"
    assert api.get(path).get_json() == original


@pytest.mark.parametrize("body", ["null", "[]", "false", "0", '"text"'])
def test_put_non_object_json(api, create_user, contract, body):
    original = create_user()
    path = f"{BASE}/{original['id']}"
    response = api.put(path, data=body, content_type="application/json")
    assert contract(response, "PUT", path, 422)["error"]["code"] == "VALIDATION_ERROR"
    assert api.get(path).get_json() == original


@pytest.mark.parametrize("body,content_type", [
    ("{broken", "application/json"), ("{}", "text/plain"),
])
def test_put_malformed_body_returns_json_400(api, create_user, body, content_type):
    original = create_user()
    path = f"{BASE}/{original['id']}"
    response = api.put(path, data=body, content_type=content_type)
    assert response.status_code == 400
    assert response.get_json()["error"]["code"] == "MALFORMED_JSON"
    assert api.get(path).get_json() == original

"""REQ-USR-05, REQ-USR-B01, REQ-USR-B02, REQ-USR-10, REQ-USR-11, REQ-USR-12."""
from datetime import datetime, timezone
from unittest.mock import Mock, patch
from uuid import uuid4

import pytest

from app.errors import UserNotFound
from app.repositories import UserRepository
from app.service import UserService


pytestmark = pytest.mark.req("REQ-USR-05")
BASE = "/api/v1/users"


@pytest.mark.parametrize("changes,expected", [
    ({"first_name": "Grace"}, {"first_name": "Grace"}),
    ({"last_name": "Hopper"}, {"last_name": "Hopper"}),
    ({"email": "NEW@EXAMPLE.COM"}, {"email": "new@example.com"}),
    ({"email": "ADA@EXAMPLE.COM"}, {"email": "ada@example.com"}),
    ({"company": None}, {"company": None}),
    ({"company": "New Co", "role": "speaker"}, {"company": "New Co", "role": "speaker"}),
])
def test_patch_changes_only_supplied_fields(api, create_user, contract, changes, expected):
    original = create_user(company="Old Co", role="organizer")
    path = f"{BASE}/{original['id']}"
    with patch("app.service.datetime") as clock:
        clock.now.return_value = datetime(2030, 1, 2, 3, 4, 5, 1, tzinfo=timezone.utc)
        updated = contract(api.patch(path, json=changes), "PATCH", path)
    assert updated == {**original, **expected, "updated_at": "2030-01-02T03:04:05.000001Z"}
    assert api.get(path).get_json() == updated


def test_empty_patch_preserves_entire_resource(api, create_user, contract):
    original = create_user()
    path = f"{BASE}/{original['id']}"
    assert contract(api.patch(path, json={}), "PATCH", path) == original
    assert api.get(path).get_json() == original


def test_patch_conflicting_email_is_atomic(api, create_user, contract):
    original = create_user(company="Old Co")
    other = create_user(email="other@example.com")
    path = f"{BASE}/{original['id']}"
    response = api.patch(path, json={"email": other["email"].upper(), "company": "New Co"})
    assert contract(response, "PATCH", path, 409)["error"]["code"] == "EMAIL_ALREADY_EXISTS"
    assert api.get(path).get_json() == original
    assert api.get(f"{BASE}/{other['id']}").get_json() == other


@pytest.mark.parametrize("payload", [{}, {"company": "New Co"}])
def test_patch_missing_user(api, contract, payload):
    path = f"{BASE}/{uuid4()}"
    assert contract(api.patch(path, json=payload), "PATCH", path, 404)["error"]["code"] == "NOT_FOUND"


@pytest.mark.parametrize("field,value", [
    ("id", "client-id"), ("created_at", "2030-01-01T00:00:00Z"),
    ("updated_at", "2030-01-01T00:00:00Z"), ("extra", True),
    ("first_name", ""), ("first_name", False), ("first_name", "a" * 51),
    ("last_name", None), ("last_name", "a" * 51), ("last_name", ""),
    ("email", None), ("email", ""), ("email", "invalid"),
    ("company", {}), ("company", "a" * 101), ("role", []),
    ("role", {}), ("role", "admin"), ("role", None),
])
def test_patch_invalid_fields_do_not_mutate(api, create_user, contract, field, value):
    original = create_user()
    path = f"{BASE}/{original['id']}"
    response = api.patch(path, json={field: value})
    assert contract(response, "PATCH", path, 422)["error"]["code"] == "VALIDATION_ERROR"
    assert api.get(path).get_json() == original


@pytest.mark.parametrize("body", ["null", "[]", "false", "0", '""'])
def test_patch_falsy_non_object_is_not_an_empty_patch(api, create_user, contract, body):
    original = create_user()
    path = f"{BASE}/{original['id']}"
    response = api.patch(path, data=body, content_type="application/json")
    assert contract(response, "PATCH", path, 422)["error"]["code"] == "VALIDATION_ERROR"
    assert api.get(path).get_json() == original


@pytest.mark.parametrize("body,content_type", [
    ("{broken", "application/json"), ("{}", "text/plain"),
])
def test_patch_malformed_json(api, create_user, body, content_type):
    original = create_user()
    path = f"{BASE}/{original['id']}"
    response = api.patch(path, data=body, content_type=content_type)
    assert response.status_code == 400
    assert response.get_json()["error"]["code"] == "MALFORMED_JSON"
    assert api.get(path).get_json() == original


@pytest.mark.parametrize("method", ["replace_user", "update_user"])
def test_update_deleted_between_read_and_write_is_not_found(method):
    """REQ-USR-04, REQ-USR-05: a concurrent deletion cannot produce a null success."""
    original = {
        "id": str(uuid4()), "first_name": "Ada", "last_name": "Lovelace",
        "email": "ada@example.com", "company": None, "role": "attendee",
        "created_at": "2026-01-01T00:00:00.000000Z",
        "updated_at": "2026-01-01T00:00:00.000000Z",
    }
    repository = Mock(spec=UserRepository)
    repository.get.return_value = original
    repository.update.return_value = None
    body = {"first_name": "Grace", "last_name": "Hopper", "email": original["email"]}
    with pytest.raises(UserNotFound):
        getattr(UserService(repository), method)(original["id"], body)

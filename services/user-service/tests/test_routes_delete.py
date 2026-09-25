"""REQ-USR-06, REQ-USR-B01, REQ-USR-08, REQ-USR-12."""
from uuid import uuid4

import pytest


pytestmark = pytest.mark.req("REQ-USR-06")
BASE = "/api/v1/users"


def test_delete_removes_only_target_and_releases_email(api, create_user, contract):
    original = create_user()
    other = create_user(email="other@example.com")
    path = f"{BASE}/{original['id']}"
    response = api.delete(path)
    assert contract(response, "DELETE", path, 204) is None
    assert response.data == b""
    assert contract(api.get(path), "GET", path, 404)["error"]["code"] == "NOT_FOUND"
    assert contract(api.delete(path), "DELETE", path, 404)["error"]["code"] == "NOT_FOUND"
    listed = contract(api.get(BASE), "GET", BASE)
    assert listed["items"] == [other] and listed["total"] == 1
    recreated = create_user(email=original["email"].upper())
    assert recreated["id"] != original["id"]
    assert recreated["email"] == original["email"]


def test_delete_missing_does_not_change_storage(api, create_user, contract):
    original = create_user()
    path = f"{BASE}/{uuid4()}"
    assert contract(api.delete(path), "DELETE", path, 404)["error"]["code"] == "NOT_FOUND"
    assert api.get(BASE).get_json()["items"] == [original]


@pytest.mark.parametrize("method,path,status,code", [
    ("GET", "/not-an-endpoint", 404, "NOT_FOUND"),
    ("POST", "/health", 405, "METHOD_NOT_ALLOWED"),
    ("PUT", BASE, 405, "METHOD_NOT_ALLOWED"),
    ("POST", f"{BASE}/missing", 405, "METHOD_NOT_ALLOWED"),
])
def test_unknown_paths_and_methods_use_error_envelope(api, method, path, status, code):
    response = api.open(path, method=method)
    assert response.status_code == status
    body = response.get_json()
    assert set(body) == {"error"}
    assert body["error"]["code"] == code
    assert isinstance(body["error"]["message"], str)
    assert isinstance(body["error"]["details"], dict)

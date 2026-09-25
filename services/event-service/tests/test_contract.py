"""REQ-EVT-02, REQ-EVT-03, REQ-EVT-04, REQ-EVT-06: complete API contract."""
from uuid import uuid4

import pytest


pytestmark = pytest.mark.req("REQ-EVT-06")
BASE = "/api/v1/events"


def test_complete_lifecycle_contract(api, payload, users_http, contract):
    contract(api.get("/health"), "GET", "/health")
    response = api.post(BASE, json=payload)
    event = contract(response, "POST", BASE, 201)
    path = response.headers["Location"]
    assert contract(api.get(path), "GET", path) == event
    assert contract(api.get(BASE), "GET", BASE)["items"] == [event]
    replaced = contract(api.put(path, json={**payload, "city": "Roma"}), "PUT", path)
    assert replaced["city"] == "Roma"
    published = contract(api.patch(path, json={"status": "published"}), "PATCH", path)
    assert published["status"] == "published" and published["city"] == "Roma"
    deleted = api.delete(path)
    assert contract(deleted, "DELETE", path, 204) is None
    assert deleted.data == b""
    assert contract(api.get(path), "GET", path, 404)["error"]["code"] == "NOT_FOUND"
    assert contract(api.delete(path), "DELETE", path, 404)["error"]["code"] == "NOT_FOUND"
    assert contract(api.get(BASE), "GET", BASE)["total"] == 0


def test_reads_and_delete_work_without_user_dependency(api, create_event, users_http, contract):
    event = create_event()
    other = create_event(title="Other event")
    users_http.reset()
    path = f"{BASE}/{event['id']}"
    contract(api.get("/health"), "GET", "/health")
    contract(api.get(path), "GET", path)
    assert contract(api.get(BASE), "GET", BASE)["total"] == 2
    contract(api.delete(path), "DELETE", path, 204)
    assert contract(api.get(BASE), "GET", BASE)["items"] == [other]
    assert len(users_http.calls) == 0


def test_delete_unknown_leaves_existing_event(api, create_event, contract):
    event = create_event()
    path = f"{BASE}/{uuid4()}"
    contract(api.delete(path), "DELETE", path, 404)
    assert api.get(BASE).get_json()["items"] == [event]


@pytest.mark.parametrize("method,path", [("PUT", BASE), ("DELETE", BASE), ("POST", f"{BASE}/missing")])
def test_unsupported_methods_have_json_errors(api, method, path):
    response = api.open(path, method=method)
    assert response.status_code == 405
    assert response.get_json()["error"]["code"] == "METHOD_NOT_ALLOWED"

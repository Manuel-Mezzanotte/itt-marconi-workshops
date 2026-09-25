"""REQ-EVT-03, REQ-EVT-B01, REQ-EVT-B02, REQ-EVT-B03, REQ-EVT-B04, REQ-EVT-B05."""
from concurrent.futures import ThreadPoolExecutor
from itertools import product
from threading import Barrier
from uuid import uuid4

import pytest


pytestmark = pytest.mark.req("REQ-EVT-03")
BASE = "/api/v1/events"


def test_put_replaces_and_resets_optional_fields(api, payload, create_event, contract, monkeypatch):
    before = create_event(description="Original description")
    path = f"{BASE}/{before['id']}"
    monkeypatch.setattr("app.service.timestamp", lambda: "2030-01-01T00:00:00.123456Z")
    body = {**payload, "title": "Replacement", "price": 25.555}
    result = contract(api.put(path, json=body), "PUT", path)
    assert result == {
        **body, "price": 25.56, "description": None, "status": "draft",
        "id": before["id"], "created_at": before["created_at"],
        "updated_at": "2030-01-01T00:00:00.123456Z",
    }
    assert api.get(path).get_json() == result


def test_put_default_cannot_revert_published(api, payload, create_event, contract):
    before = create_event(status="published")
    path = f"{BASE}/{before['id']}"
    error = contract(api.put(path, json=payload), "PUT", path, 422)
    assert error["error"]["code"] == "INVALID_STATUS_TRANSITION"
    assert api.get(path).get_json() == before


def test_patch_preserves_other_fields_and_empty_is_noop(api, create_event, users_http, contract, monkeypatch):
    before = create_event(description="Original", status="published")
    path = f"{BASE}/{before['id']}"
    users_http.reset()
    assert contract(api.patch(path, json={}), "PATCH", path) == before
    monkeypatch.setattr("app.service.timestamp", lambda: "2030-01-01T00:00:00.000001Z")
    changed = contract(api.patch(path, json={"description": None, "capacity": 200}), "PATCH", path)
    assert changed == {
        **before, "description": None, "capacity": 200, "updated_at": "2030-01-01T00:00:00.000001Z",
    }
    assert len(users_http.calls) == 0


@pytest.mark.parametrize("changes", [
    {"start_date": "2026-11-12"}, {"end_date": "2026-11-09"},
])
@pytest.mark.req("REQ-EVT-B03")
def test_patch_dates_validated_after_merge(api, create_event, contract, changes):
    before = create_event()
    path = f"{BASE}/{before['id']}"
    assert contract(api.patch(path, json=changes), "PATCH", path, 422)["error"]["code"] == "VALIDATION_ERROR"
    assert api.get(path).get_json() == before
    updated = contract(api.patch(path, json={
        "start_date": "2026-12-01", "end_date": "2026-12-02",
    }), "PATCH", path)
    assert updated["start_date"] == "2026-12-01"


@pytest.mark.parametrize("method", ["PUT", "PATCH"])
@pytest.mark.parametrize("previous,target", list(product(["draft", "published", "cancelled"], repeat=2)))
@pytest.mark.req("REQ-EVT-B04")
def test_state_transitions_on_both_methods(api, payload, create_event, contract, method, previous, target):
    before = create_event(status=previous)
    path = f"{BASE}/{before['id']}"
    body = {**(payload if method == "PUT" else {}), "status": target}
    allowed = previous == target or (previous, target) in {
        ("draft", "published"), ("draft", "cancelled"), ("published", "cancelled"),
    }
    result = contract(api.open(path, method=method, json=body), method, path, 200 if allowed else 422)
    if allowed:
        assert result["status"] == target
    else:
        assert result["error"]["code"] == "INVALID_STATUS_TRANSITION"
        assert api.get(path).get_json() == before


@pytest.mark.parametrize("method", ["PUT", "PATCH"])
@pytest.mark.parametrize("status,body,expected,code", [
    (404, {}, 422, "REFERENCE_NOT_FOUND"),
    (200, {"role": "attendee"}, 422, "INVALID_ORGANIZER"),
    (503, {}, 503, "DEPENDENCY_UNAVAILABLE"),
])
@pytest.mark.req("REQ-EVT-B01")
@pytest.mark.req("REQ-EVT-B02")
@pytest.mark.req("REQ-EVT-B05")
def test_organizer_failures_do_not_modify(api, payload, create_event, users_http, contract,
                                       method, status, body, expected, code):
    before = create_event()
    path = f"{BASE}/{before['id']}"
    users_http.reset()
    organizer = str(uuid4())
    users_http.get(f"http://users.test:9001/api/v1/users/{organizer}", status=status, json=body)
    data = {**(payload if method == "PUT" else {}), "organizer_id": organizer, "title": "Changed"}
    result = contract(api.open(path, method=method, json=data), method, path, expected)
    assert result["error"]["code"] == code
    assert api.get(path).get_json() == before


def test_patch_changes_organizer(api, create_event, users_http, contract):
    before = create_event()
    organizer = str(uuid4())
    users_http.get(f"http://users.test:9001/api/v1/users/{organizer}", json={"role": "organizer"})
    path = f"{BASE}/{before['id']}"
    assert contract(api.patch(path, json={"organizer_id": organizer.upper()}), "PATCH", path)["organizer_id"] == organizer


@pytest.mark.parametrize("method", ["PUT", "PATCH"])
@pytest.mark.parametrize("field,value", [
    ("id", "client"), ("created_at", "date"), ("updated_at", "date"), ("extra", 1),
    ("title", "ab"), ("capacity", True), ("price", -1), ("status", []),
])
def test_invalid_update_is_atomic(api, payload, create_event, contract, method, field, value):
    before = create_event()
    path = f"{BASE}/{before['id']}"
    data = {**(payload if method == "PUT" else {}), field: value}
    result = contract(api.open(path, method=method, json=data), method, path, 422)
    assert result["error"]["code"] == "VALIDATION_ERROR"
    assert api.get(path).get_json() == before


@pytest.mark.parametrize("method", ["PUT", "PATCH"])
@pytest.mark.parametrize("body,status", [("null", 422), ("[]", 422), ("false", 422), ("{broken", 400)])
def test_invalid_body(api, create_event, contract, method, body, status):
    before = create_event()
    path = f"{BASE}/{before['id']}"
    response = api.open(path, method=method, data=body, content_type="application/json")
    assert response.status_code == status
    if status == 422:
        contract(response, method, path, status)
    assert response.get_json()["error"]["code"] == ("MALFORMED_JSON" if status == 400 else "VALIDATION_ERROR")
    assert api.get(path).get_json() == before


@pytest.mark.parametrize("method", ["PUT", "PATCH"])
def test_unknown_id_and_disappearance_at_write(api, payload, create_event, contract, monkeypatch, method):
    path = f"{BASE}/{uuid4()}"
    contract(api.open(path, method=method, json=payload), method, path, 404)
    before = create_event()
    path = f"{BASE}/{before['id']}"
    monkeypatch.setattr(api.application.extensions["event_repository"], "update", lambda *args: None)
    contract(api.open(path, method=method, json=payload), method, path, 404)


@pytest.mark.req("REQ-EVT-B04")
def test_concurrent_publication_cannot_revive_cancelled_event(api, create_event, contract, monkeypatch):
    before = create_event()
    path = f"{BASE}/{before['id']}"
    repository = api.application.extensions["event_repository"]
    update = repository.update
    barrier = Barrier(2)

    def simultaneous_update(*args):
        barrier.wait(timeout=3)
        return update(*args)

    monkeypatch.setattr(repository, "update", simultaneous_update)

    def change(status):
        with api.application.test_client() as client:
            return client.patch(path, json={"status": status})

    with ThreadPoolExecutor(max_workers=2) as pool:
        published, cancelled = list(pool.map(change, ["published", "cancelled"]))
    contract(cancelled, "PATCH", path)
    contract(published, "PATCH", path, published.status_code)
    assert published.status_code in (200, 422)
    if published.status_code == 422:
        assert published.get_json()["error"]["code"] == "INVALID_STATUS_TRANSITION"
    assert api.get(path).get_json()["status"] == "cancelled"

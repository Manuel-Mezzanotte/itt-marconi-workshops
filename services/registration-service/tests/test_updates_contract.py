"""REQ-REG-03, REQ-REG-B04..B07, REQ-REG-04, REQ-REG-05."""
from uuid import uuid4

import pytest


pytestmark = pytest.mark.req("REQ-REG-03")
BASE = "/api/v1/registrations"


def test_cancellation_is_idempotent_and_cannot_reactivate(api, create_registration, references, contract, monkeypatch):
    original = create_registration()
    path = f"{BASE}/{original['id']}"
    references.reset()
    assert contract(api.patch(path, json={"status": "confirmed"}), "PATCH", path) == original
    monkeypatch.setattr("app.service.timestamp", lambda: "2030-01-01T00:00:00.123456Z")
    cancelled = contract(api.patch(path, json={"status": "cancelled"}), "PATCH", path)
    assert cancelled == {**original, "status": "cancelled", "updated_at": "2030-01-01T00:00:00.123456Z"}
    monkeypatch.setattr("app.service.timestamp", lambda: "2031-01-01T00:00:00.000000Z")
    assert contract(api.patch(path, json={"status": "cancelled"}), "PATCH", path) == cancelled
    error = contract(api.patch(path, json={"status": "confirmed"}), "PATCH", path, 422)
    assert error["error"]["code"] == "INVALID_STATUS_TRANSITION"
    assert api.get(path).get_json() == cancelled
    assert len(references.calls) == 0


def test_cancel_then_same_user_reregisters_and_historical_delete_does_not_free_seat(
    api, payload, event, create_registration, contract,
):
    event["capacity"] = 1
    first = create_registration()
    path = f"{BASE}/{first['id']}"
    contract(api.patch(path, json={"status": "cancelled"}), "PATCH", path)
    second = create_registration()
    assert second["id"] != first["id"]
    items = contract(api.get(BASE, query_string=payload), "GET", BASE)["items"]
    assert [item["status"] for item in items] == ["cancelled", "confirmed"]
    contract(api.delete(path), "DELETE", path, 204)
    response = api.post(BASE, json={**payload, "user_id": str(uuid4())})
    assert contract(response, "POST", BASE, 409)["error"]["code"] == "EVENT_FULL"


def test_delete_confirmed_frees_seat_and_is_local(api, payload, event, create_registration, references, contract):
    event["capacity"] = 1
    original = create_registration()
    path = f"{BASE}/{original['id']}"
    before = len(references.calls)
    response = api.delete(path)
    assert contract(response, "DELETE", path, 204) is None and response.data == b""
    assert contract(api.get(path), "GET", path, 404)["error"]["code"] == "NOT_FOUND"
    contract(api.delete(path), "DELETE", path, 404)
    assert len(references.calls) == before
    replacement = create_registration(user_id=str(uuid4()))
    assert api.get(BASE).get_json()["items"] == [replacement]


def test_amount_remains_historical(api, event, create_registration, contract):
    old = create_registration()
    event["price"] = 249.99
    new = create_registration(user_id=str(uuid4()))
    assert new["amount"] == 249.99
    path = f"{BASE}/{old['id']}"
    assert contract(api.get(path), "GET", path)["amount"] == 149.0
    assert contract(api.patch(path, json={"status": "cancelled"}), "PATCH", path)["amount"] == 149.0


@pytest.mark.parametrize("body", [
    {}, {"status": "other"}, {"status": []}, {"status": {}},
    {"status": "cancelled", "id": "client"},
    {"status": "cancelled", "amount": 0}, {"status": "cancelled", "user_id": "client"},
    {"status": "cancelled", "event_id": "client"},
    {"status": "cancelled", "created_at": "client"},
    {"status": "cancelled", "updated_at": "client"},
])
def test_patch_invalid_body_keeps_record(api, create_registration, contract, body):
    original = create_registration()
    path = f"{BASE}/{original['id']}"
    assert contract(api.patch(path, json=body), "PATCH", path, 422)["error"]["code"] == "VALIDATION_ERROR"
    assert api.get(path).get_json() == original


@pytest.mark.parametrize("body,content_type,status", [
    ("null", "application/json", 422), ("[]", "application/json", 422),
    ("false", "application/json", 422), ("{broken", "application/json", 400),
    ("{}", "text/plain", 400),
])
def test_patch_parsing(api, create_registration, contract, body, content_type, status):
    original = create_registration()
    path = f"{BASE}/{original['id']}"
    response = api.patch(path, data=body, content_type=content_type)
    assert response.status_code == status
    if status == 422:
        contract(response, "PATCH", path, status)
    assert response.get_json()["error"]["code"] == ("VALIDATION_ERROR" if status == 422 else "MALFORMED_JSON")
    assert api.get(path).get_json() == original


def test_unknown_ids_and_put_405(api, create_registration, contract):
    path = f"{BASE}/{uuid4()}"
    contract(api.patch(path, json={"status": "cancelled"}), "PATCH", path, 404)
    contract(api.delete(path), "DELETE", path, 404)
    assert contract(api.put(path), "PUT", path, 405)["error"]["code"] == "METHOD_NOT_ALLOWED"
    original = create_registration()
    path = f"{BASE}/{original['id']}"
    contract(api.put(path, json={"status": "cancelled"}), "PUT", path, 405)
    assert api.get(path).get_json() == original


def test_all_eight_contract_operations_in_capacity_journey(api, payload, references, contract):
    contract(api.get("/health"), "GET", "/health")
    first = contract(api.post(BASE, json=payload), "POST", BASE, 201)
    second = contract(api.post(BASE, json={**payload, "user_id": str(uuid4())}), "POST", BASE, 201)
    third = {**payload, "user_id": str(uuid4())}
    assert contract(api.post(BASE, json=third), "POST", BASE, 409)["error"]["code"] == "EVENT_FULL"
    path = f"{BASE}/{first['id']}"
    assert contract(api.get(path), "GET", path) == first
    contract(api.put(path), "PUT", path, 405)
    contract(api.patch(path, json={"status": "cancelled"}), "PATCH", path)
    replacement = contract(api.post(BASE, json=third), "POST", BASE, 201)
    active = contract(api.get(BASE, query_string={"status": "confirmed"}), "GET", BASE)
    assert active["items"] == [second, replacement] and active["total"] == 2
    stats_path = f"{BASE}/stats"
    assert contract(api.get(stats_path, query_string={"event_id": payload["event_id"]}), "GET", stats_path) == {
        "event_id": payload["event_id"], "capacity": 2, "confirmed": 2, "available": 0,
    }
    assert contract(api.delete(path), "DELETE", path, 204) is None

"""REQ-REG-01, REQ-REG-B01..B06, REQ-REG-B09, REQ-REG-05."""
from datetime import datetime
from unittest.mock import patch
from uuid import UUID, uuid4

import pytest
import requests
import responses


pytestmark = pytest.mark.req("REQ-REG-01")
BASE = "/api/v1/registrations"


@pytest.mark.parametrize("price", [0, 149.0, 25.55])
def test_creation_amount_and_contract(api, payload, event, references, contract, price):
    event["price"] = price
    with patch("app.clients.requests.get", wraps=requests.get) as get:
        response = api.post(BASE, json={key: value.upper() for key, value in payload.items()})
    registration = contract(response, "POST", BASE, 201)
    assert registration == {**payload, "id": registration["id"], "amount": price, "status": "confirmed",
                            "created_at": registration["created_at"], "updated_at": registration["updated_at"]}
    assert UUID(registration["id"]).version == 4
    assert registration["created_at"] == registration["updated_at"]
    assert registration["created_at"].endswith("Z")
    assert datetime.fromisoformat(registration["created_at"]).utcoffset().total_seconds() == 0
    assert response.headers["Location"] == f"{BASE}/{registration['id']}"
    assert [call.args[0] for call in get.call_args_list] == [
        f"http://users.test:9001/api/v1/users/{payload['user_id']}",
        f"http://events.test:9002/api/v1/events/{payload['event_id']}",
    ]
    assert all(call.kwargs == {"timeout": 2, "allow_redirects": False} for call in get.call_args_list)


@pytest.mark.parametrize("dependency", ["users", "events"])
@pytest.mark.parametrize("status,body,expected,code", [
    (404, {}, 422, "REFERENCE_NOT_FOUND"),
    (500, {}, 503, "DEPENDENCY_UNAVAILABLE"), (503, {}, 503, "DEPENDENCY_UNAVAILABLE"),
    (302, {}, 503, "DEPENDENCY_UNAVAILABLE"),
    (200, {}, 503, "DEPENDENCY_UNAVAILABLE"), (200, [], 503, "DEPENDENCY_UNAVAILABLE"),
    (200, {"id": "different"}, 503, "DEPENDENCY_UNAVAILABLE"),
])
def test_dependency_errors(api, payload, event, contract, dependency, status, body, expected, code):
    with responses.RequestsMock() as mock:
        if dependency == "events":
            mock.get(f"http://users.test:9001/api/v1/users/{payload['user_id']}",
                     json={"id": payload["user_id"]})
        identifier = payload["user_id" if dependency == "users" else "event_id"]
        host = "users.test:9001" if dependency == "users" else "events.test:9002"
        mock.get(f"http://{host}/api/v1/{dependency}/{identifier}", status=status, json=body)
        result = contract(api.post(BASE, json=payload), "POST", BASE, expected)
    assert result["error"]["code"] == code
    assert api.application.extensions["registration_repository"].list({}, 1, 20) == ([], 0)


@pytest.mark.parametrize("dependency", ["users", "events"])
@pytest.mark.parametrize("failure", [requests.Timeout("timeout"), requests.ConnectionError("refused"), "not JSON"])
def test_transport_and_body_failures(api, payload, contract, dependency, failure):
    with responses.RequestsMock() as mock:
        if dependency == "events":
            mock.get(f"http://users.test:9001/api/v1/users/{payload['user_id']}",
                     json={"id": payload["user_id"]})
        identifier = payload["user_id" if dependency == "users" else "event_id"]
        host = "users.test:9001" if dependency == "users" else "events.test:9002"
        mock.get(f"http://{host}/api/v1/{dependency}/{identifier}", body=failure)
        assert contract(api.post(BASE, json=payload), "POST", BASE, 503)["error"]["code"] == "DEPENDENCY_UNAVAILABLE"


@pytest.mark.parametrize("field,value", [
    ("capacity", True), ("capacity", 0), ("capacity", 10001), ("capacity", 1.5),
    ("price", "149"), ("price", -1), ("price", True), ("price", float("nan")),
    ("price", float("inf")), ("price", 10**400), ("status", []), ("status", "other"),
])
def test_invalid_event_data_is_dependency_error(api, payload, event, references, contract, field, value):
    event[field] = value
    assert contract(api.post(BASE, json=payload), "POST", BASE, 503)["error"]["code"] == "DEPENDENCY_UNAVAILABLE"


@pytest.mark.parametrize("status", ["draft", "cancelled"])
def test_event_not_open(api, payload, event, references, contract, status):
    event["status"] = status
    assert contract(api.post(BASE, json=payload), "POST", BASE, 422)["error"]["code"] == "EVENT_NOT_OPEN"
    assert api.application.extensions["registration_repository"].count_confirmed(payload["event_id"]) == 0


def test_duplicate_priority_capacity_and_separate_events(api, payload, event, references, contract):
    event["capacity"] = 1
    first = contract(api.post(BASE, json=payload), "POST", BASE, 201)
    assert contract(api.post(BASE, json=payload), "POST", BASE, 409)["error"]["code"] == "ALREADY_REGISTERED"
    another = {**payload, "user_id": str(uuid4())}
    assert contract(api.post(BASE, json=another), "POST", BASE, 409)["error"]["code"] == "EVENT_FULL"
    other_event = contract(api.post(BASE, json={**payload, "event_id": str(uuid4())}), "POST", BASE, 201)
    assert other_event["id"] != first["id"]


@pytest.mark.parametrize("field", ["id", "amount", "status", "created_at", "updated_at", "extra"])
def test_readonly_fields_rejected_before_http(api, payload, contract, field):
    with responses.RequestsMock() as mock:
        response = contract(api.post(BASE, json={**payload, field: "client"}), "POST", BASE, 422)
        assert len(mock.calls) == 0
    assert response["error"]["code"] == "VALIDATION_ERROR"


@pytest.mark.parametrize("body,content_type,status", [
    ("{broken", "application/json", 400), ("{}", "text/plain", 400),
    ("null", "application/json", 422), ("[]", "application/json", 422),
])
def test_body_errors(api, contract, body, content_type, status):
    result = contract(api.post(BASE, data=body, content_type=content_type), "POST", BASE, status)
    assert result["error"]["code"] == ("MALFORMED_JSON" if status == 400 else "VALIDATION_ERROR")

"""REQ-EVT-01, REQ-EVT-B01, REQ-EVT-B02, REQ-EVT-B05, REQ-EVT-04, REQ-EVT-06."""
from datetime import datetime
from unittest.mock import patch
from uuid import UUID

import pytest
import requests
import responses


pytestmark = pytest.mark.req("REQ-EVT-01")
BASE = "/api/v1/events"


@pytest.mark.parametrize("status", [None, "published", "cancelled"])
def test_post_contract_defaults_and_explicit_status(api, payload, users_http, contract, status):
    if status is not None:
        payload["status"] = status
    with patch("app.clients.requests.get", wraps=requests.get) as get:
        response = api.post(BASE, json=payload)
    event = contract(response, "POST", BASE, 201)
    assert event == {**payload, "description": None, "status": status or "draft",
                     "id": event["id"], "created_at": event["created_at"], "updated_at": event["updated_at"]}
    assert UUID(event["id"]).version == 4
    assert event["created_at"] == event["updated_at"]
    assert event["created_at"].endswith("Z")
    assert datetime.fromisoformat(event["created_at"]).utcoffset().total_seconds() == 0
    assert response.headers["Location"] == f"{BASE}/{event['id']}"
    get.assert_called_once_with(
        f"http://users.test:9001/api/v1/users/{payload['organizer_id']}",
        timeout=2, allow_redirects=False,
    )
    assert api.application.extensions["event_repository"].get(event["id"]) == event


@pytest.mark.parametrize("response_status,body,status,code", [
    (404, {}, 422, "REFERENCE_NOT_FOUND"),
    (200, {"role": "attendee"}, 422, "INVALID_ORGANIZER"),
    (200, {"role": "speaker"}, 422, "INVALID_ORGANIZER"),
    (500, {}, 503, "DEPENDENCY_UNAVAILABLE"),
    (503, {}, 503, "DEPENDENCY_UNAVAILABLE"),
    (302, {}, 503, "DEPENDENCY_UNAVAILABLE"),
    (200, {}, 503, "DEPENDENCY_UNAVAILABLE"),
    (200, [], 503, "DEPENDENCY_UNAVAILABLE"),
    (200, {"role": []}, 503, "DEPENDENCY_UNAVAILABLE"),
])
def test_upstream_errors_do_not_create(api, payload, contract, response_status, body, status, code):
    with responses.RequestsMock() as mock:
        mock.get(f"http://users.test:9001/api/v1/users/{payload['organizer_id']}",
                 json=body, status=response_status)
        result = contract(api.post(BASE, json=payload), "POST", BASE, status)
    assert result["error"]["code"] == code
    assert api.application.extensions["event_repository"].list({}, 1, 20) == ([], 0)


@pytest.mark.parametrize("failure", [requests.Timeout("timeout"), requests.ConnectionError("refused"), "not JSON"])
def test_dependency_transport_and_invalid_json(api, payload, contract, failure):
    with responses.RequestsMock() as mock:
        mock.get(f"http://users.test:9001/api/v1/users/{payload['organizer_id']}", body=failure)
        result = contract(api.post(BASE, json=payload), "POST", BASE, 503)
    assert result["error"]["code"] == "DEPENDENCY_UNAVAILABLE"
    assert api.application.extensions["event_repository"].list({}, 1, 20) == ([], 0)


@pytest.mark.parametrize("field,value", [
    ("id", "client-id"), ("created_at", "client-date"), ("updated_at", "client-date"),
    ("extra", 1), ("capacity", True), ("price", float("nan")),
    ("organizer_id", "bad"), ("end_date", "2020-01-01"),
])
def test_local_validation_precedes_http(api, payload, contract, field, value):
    with responses.RequestsMock() as mock:
        result = contract(api.post(BASE, json={**payload, field: value}), "POST", BASE, 422)
        assert len(mock.calls) == 0
    assert result["error"]["code"] == "VALIDATION_ERROR"
    assert api.application.extensions["event_repository"].list({}, 1, 20) == ([], 0)


@pytest.mark.parametrize("body,content_type,status", [
    ("{broken", "application/json", 400), ("{}", "text/plain", 400),
    ("null", "application/json", 422), ("[]", "application/json", 422),
    ("false", "application/json", 422),
])
def test_body_errors(api, contract, body, content_type, status):
    response = api.post(BASE, data=body, content_type=content_type)
    result = contract(response, "POST", BASE, status)
    assert result["error"]["code"] == ("MALFORMED_JSON" if status == 400 else "VALIDATION_ERROR")

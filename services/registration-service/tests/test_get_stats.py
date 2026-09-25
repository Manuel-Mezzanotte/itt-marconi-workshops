"""REQ-REG-02, REQ-REG-B08, REQ-REG-B09, REQ-REG-05."""
from uuid import uuid4

import pytest
import requests
import responses


pytestmark = pytest.mark.req("REQ-REG-02")
BASE = "/api/v1/registrations"


def test_get_and_list_do_not_call_dependencies(api, create_registration, references, contract):
    registration = create_registration()
    references.reset()
    path = f"{BASE}/{registration['id']}"
    assert contract(api.get(path), "GET", path) == registration
    assert contract(api.get(BASE), "GET", BASE) == {
        "items": [registration], "page": 1, "page_size": 20, "total": 1,
    }
    missing = f"{BASE}/{uuid4()}"
    assert contract(api.get(missing), "GET", missing, 404)["error"]["code"] == "NOT_FOUND"
    assert len(references.calls) == 0


def test_empty_list(api, contract):
    assert contract(api.get(BASE), "GET", BASE) == {
        "items": [], "page": 1, "page_size": 20, "total": 0,
    }


def test_filters_pagination_and_totals(api, payload, event, create_registration, contract):
    event["capacity"] = 100
    records = [create_registration(user_id=str(uuid4())) for _ in range(23)]
    another_event = str(uuid4())
    extra = create_registration(event_id=another_event, user_id=records[0]["user_id"])
    records.append(extra)
    records.sort(key=lambda record: (record["created_at"], record["id"]))
    queries = [
        {}, {"user_id": records[0]["user_id"]}, {"event_id": payload["event_id"]},
        {"status": "cancelled"},
        {"user_id": records[0]["user_id"], "event_id": another_event, "status": "confirmed"},
    ]
    for query in queries:
        expected = [item for item in records if all(item[key] == value for key, value in query.items())]
        result = contract(api.get(BASE, query_string=query), "GET", BASE)
        assert result == {"items": expected[:20], "page": 1, "page_size": 20, "total": len(expected)}
        second = contract(api.get(BASE, query_string={**query, "page": 2}), "GET", BASE)
        assert second["items"] == expected[20:] and second["total"] == len(expected)
    result = contract(api.get(BASE, query_string={"event_id": another_event.upper()}), "GET", BASE)
    assert result["items"] == [extra]
    result = contract(api.get(BASE, query_string={"page_size": 100}), "GET", BASE)
    assert result["items"] == records
    result = contract(api.get(BASE, query_string={"page": 10**30}), "GET", BASE)
    assert result["items"] == [] and result["total"] == 24


@pytest.mark.parametrize("query", [
    {"page": ""}, {"page": 0}, {"page": -1}, {"page": "1.5"}, {"page": "bad"},
    {"page_size": ""}, {"page_size": 0}, {"page_size": 101}, {"page_size": "bad"},
    {"user_id": ""}, {"user_id": "bad"}, {"event_id": "bad"},
    {"status": ""}, {"status": "other"},
])
def test_invalid_query(api, query, contract):
    assert contract(api.get(BASE, query_string=query), "GET", BASE, 422)["error"]["code"] == "VALIDATION_ERROR"


def test_stats_counts_and_capacity_reduction(api, payload, event, create_registration, contract):
    create_registration()
    create_registration(user_id=str(uuid4()))
    path = f"{BASE}/stats"
    assert contract(api.get(path, query_string={"event_id": payload["event_id"].upper()}), "GET", path) == {
        "event_id": payload["event_id"], "capacity": 2, "confirmed": 2, "available": 0,
    }
    event["capacity"] = 1
    result = contract(api.get(path, query_string={"event_id": payload["event_id"]}), "GET", path)
    assert result["confirmed"] == 2 and result["available"] == 0


@pytest.mark.parametrize("status", ["draft", "published", "cancelled"])
def test_stats_on_empty_event_uses_only_event_service(api, payload, event, references, contract, status):
    event["status"] = status
    path = f"{BASE}/stats"
    result = contract(api.get(path, query_string={"event_id": payload["event_id"]}), "GET", path)
    assert result == {"event_id": payload["event_id"], "capacity": 2, "confirmed": 0, "available": 2}
    assert len(references.calls) == 1
    assert references.calls[0].request.url.startswith("http://events.test:9002/")


@pytest.mark.parametrize("query", [{}, {"event_id": ""}, {"event_id": "bad"}])
def test_stats_requires_valid_event_id(api, query, contract):
    path = f"{BASE}/stats"
    assert contract(api.get(path, query_string=query), "GET", path, 422)["error"]["code"] == "VALIDATION_ERROR"


@pytest.mark.parametrize("status,body,expected,code", [
    (404, {}, 404, "NOT_FOUND"),
    (503, {}, 503, "DEPENDENCY_UNAVAILABLE"),
    (200, requests.Timeout("timeout"), 503, "DEPENDENCY_UNAVAILABLE"),
])
def test_stats_missing_or_unavailable_event(api, payload, contract, status, body, expected, code):
    path = f"{BASE}/stats"
    with responses.RequestsMock() as mock:
        kwargs = {"body": body} if isinstance(body, Exception) else {"json": body}
        mock.get(f"http://events.test:9002/api/v1/events/{payload['event_id']}", status=status, **kwargs)
        result = contract(api.get(path, query_string={"event_id": payload["event_id"]}), "GET", path, expected)
    assert result["error"]["code"] == code

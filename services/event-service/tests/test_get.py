"""REQ-EVT-02, REQ-EVT-B06, REQ-EVT-06."""
from uuid import uuid4

import pytest


pytestmark = pytest.mark.req("REQ-EVT-02")
BASE = "/api/v1/events"


def test_single_event_and_missing(api, create_event, users_http, contract):
    event = create_event()
    calls = len(users_http.calls)
    path = f"{BASE}/{event['id']}"
    assert contract(api.get(path), "GET", path) == event
    path = f"{BASE}/{uuid4()}"
    assert contract(api.get(path), "GET", path, 404)["error"]["code"] == "NOT_FOUND"
    assert len(users_http.calls) == calls


def test_empty_list(api, contract):
    assert contract(api.get(BASE), "GET", BASE) == {
        "items": [], "page": 1, "page_size": 20, "total": 0,
    }


@pytest.mark.req("REQ-EVT-B06")
def test_pagination_and_filters(api, create_event, contract):
    events = [create_event(title=f"Conference {number}", status="published" if number % 2 else "draft",
                           city="Roma" if number % 3 else "Trento") for number in range(23)]
    events.sort(key=lambda event: (event["created_at"], event["id"]))
    for query in ({}, {"status": "published"}, {"city": "Roma"},
                  {"city": "Trento", "status": "draft"}):
        expected = [event for event in events if all(event[key] == value for key, value in query.items())]
        result = contract(api.get(BASE, query_string=query), "GET", BASE)
        assert result == {"items": expected[:20], "page": 1, "page_size": 20, "total": len(expected)}
        second = contract(api.get(BASE, query_string={**query, "page": 2}), "GET", BASE)
        assert second["items"] == expected[20:] and second["total"] == len(expected)
    all_events = contract(api.get(BASE, query_string={"page_size": 100}), "GET", BASE)
    assert all_events["items"] == events and all_events["page_size"] == 100
    beyond = contract(api.get(BASE, query_string={"page": 10**30}), "GET", BASE)
    assert beyond["items"] == [] and beyond["total"] == 23
    assert api.get(BASE, query_string={"city": "roma"}).get_json()["items"] == []


@pytest.mark.req("REQ-EVT-B06")
def test_empty_city_is_distinct_from_no_filter(api, create_event, contract):
    empty = create_event(city="")
    create_event(city="Trento")
    assert api.get(BASE).get_json()["total"] == 2
    result = contract(api.get(BASE, query_string={"city": ""}), "GET", BASE)
    assert result["items"] == [empty] and result["total"] == 1


@pytest.mark.parametrize("query", [
    {"page": ""}, {"page": "bad"}, {"page": "1.5"}, {"page": 0}, {"page": -1},
    {"page_size": ""}, {"page_size": "bad"}, {"page_size": "1.5"},
    {"page_size": 0}, {"page_size": -1}, {"page_size": 101},
    {"status": ""}, {"status": "PUBLISHED"}, {"status": "unknown"},
])
def test_invalid_query(api, contract, query):
    result = contract(api.get(BASE, query_string=query), "GET", BASE, 422)
    assert result["error"]["code"] == "VALIDATION_ERROR"

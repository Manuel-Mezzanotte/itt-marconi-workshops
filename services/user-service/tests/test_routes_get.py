"""REQ-USR-02, REQ-USR-03, REQ-USR-B02, REQ-USR-B03, REQ-USR-12."""
from uuid import uuid4

import pytest


pytestmark = pytest.mark.req("REQ-USR-03")
BASE = "/api/v1/users"


def test_get_existing_and_missing(api, create_user, contract):
    user = create_user()
    path = f"{BASE}/{user['id']}"
    assert contract(api.get(path), "GET", path) == user
    missing = f"{BASE}/{uuid4()}"
    assert contract(api.get(missing), "GET", missing, 404)["error"]["code"] == "NOT_FOUND"


def test_empty_list_defaults(api, contract):
    assert contract(api.get(BASE), "GET", BASE) == {
        "items": [], "page": 1, "page_size": 20, "total": 0,
    }


def test_pagination_stable_and_total_before_slice(api, create_user, contract):
    users = [create_user(email=f"person{i}@example.com") for i in range(23)]
    expected = sorted(users, key=lambda user: (user["created_at"], user["id"]))
    first = contract(api.get(BASE), "GET", BASE)
    second = contract(api.get(BASE, query_string={"page": 2}), "GET", BASE)
    assert first["items"] == expected[:20]
    assert second["items"] == expected[20:]
    assert first["total"] == second["total"] == 23
    assert second["page"] == 2 and second["page_size"] == 20
    assert api.get(BASE).get_json() == first
    for page in (3, 10**30):
        result = contract(api.get(BASE, query_string={"page": page}), "GET", BASE)
        assert result == {"items": [], "page": page, "page_size": 20, "total": 23}
    largest = contract(api.get(BASE, query_string={"page_size": 100}), "GET", BASE)
    assert largest["items"] == expected and largest["page_size"] == 100


def test_filters_combine_and_preserve_empty_email(api, create_user, contract):
    organizer = create_user(role="organizer", email="ORG@example.com")
    speaker = create_user(role="speaker", email="speaker@example.com")
    create_user(email="attendee@example.com")
    cases = [
        ({"role": "organizer"}, [organizer]),
        ({"email": "ORG@EXAMPLE.COM"}, [organizer]),
        ({"email": speaker["email"], "role": "speaker"}, [speaker]),
        ({"email": speaker["email"], "role": "organizer"}, []),
        ({"email": ""}, []),
        ({"email": "missing@example.com"}, []),
    ]
    for query, expected in cases:
        result = contract(api.get(BASE, query_string=query), "GET", BASE)
        assert result["items"] == expected
        assert result["total"] == len(expected)
    result = contract(api.get(BASE, query_string={
        "role": "organizer", "page_size": 1, "page": 2,
    }), "GET", BASE)
    assert result["items"] == [] and result["total"] == 1


@pytest.mark.parametrize("query", [
    {"page": "0"}, {"page": "-1"}, {"page": ""}, {"page": "1.5"},
    {"page": "abc"}, {"page_size": "0"}, {"page_size": "-1"},
    {"page_size": ""}, {"page_size": "abc"}, {"page_size": "101"},
    {"page_size": "1.5"}, {"role": ""}, {"role": "admin"}, {"role": "ORGANIZER"},
])
def test_invalid_query_returns_422(api, query, contract):
    result = contract(api.get(BASE, query_string=query), "GET", BASE, 422)
    assert result["error"]["code"] == "VALIDATION_ERROR"

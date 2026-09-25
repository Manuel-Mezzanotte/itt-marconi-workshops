"""REQ-EVT-01, REQ-EVT-B03, REQ-EVT-B04."""
from copy import deepcopy
from itertools import product

import pytest

from app.errors import ApiError
from app.validation import STATUSES, validate_event, validate_transition


pytestmark = pytest.mark.req("REQ-EVT-01")


def test_valid_boundary_values_and_input_unchanged(payload):
    payload.update(title="a" * 120, description="a" * 2000, venue="a" * 100,
                   city="a" * 60, capacity=10000, price=1.005,
                   start_date="2028-02-29", end_date="2028-02-29",
                   organizer_id=payload["organizer_id"].upper())
    before = deepcopy(payload)
    result = validate_event(payload)
    assert payload == before
    assert result["price"] == 1.01
    assert result["organizer_id"] == payload["organizer_id"].lower()
    assert result["status"] == "draft"
    minimum = {**payload, "title": "abc", "description": None, "venue": "", "city": "",
               "capacity": 1, "price": 0}
    assert validate_event(minimum)["price"] == 0


@pytest.mark.parametrize("field,value", [
    ("title", ""), ("title", "ab"), ("title", "a" * 121), ("title", None),
    ("description", "a" * 2001), ("description", 1), ("venue", "a" * 101),
    ("city", "a" * 61), ("city", []), ("organizer_id", "not-a-uuid"),
    ("organizer_id", "12345678123442348234123456789abc"), ("organizer_id", None),
    ("start_date", "2026-02-29"), ("end_date", "2026-13-01"),
    ("start_date", "20261110"), ("end_date", False), ("end_date", "2026-11-09"),
    ("capacity", 0), ("capacity", 10001), ("capacity", 1.0), ("capacity", True),
    ("price", -0.01), ("price", "149"), ("price", True),
    ("price", float("nan")), ("price", float("inf")), ("price", 10**400),
    ("status", "other"), ("status", []), ("status", {}),
    ("id", "client"), ("created_at", "2026-01-01T00:00:00Z"), ("updated_at", "ignored"),
])
@pytest.mark.req("REQ-EVT-B03")
def test_invalid_fields(payload, field, value):
    with pytest.raises(ApiError) as error:
        validate_event({**payload, field: value})
    assert error.value.status == 422 and error.value.code == "VALIDATION_ERROR"


@pytest.mark.parametrize("field", [
    "title", "organizer_id", "venue", "city", "start_date", "end_date", "capacity", "price",
])
def test_missing_required(payload, field):
    del payload[field]
    with pytest.raises(ApiError):
        validate_event(payload)


@pytest.mark.parametrize("body", [None, [], False, 1, "text"])
def test_non_object(body):
    with pytest.raises(ApiError):
        validate_event(body)


def test_partial_validates_only_present_fields():
    assert validate_event({}, partial=True) == {}
    assert validate_event({"description": None}, partial=True) == {"description": None}
    assert validate_event({"end_date": "2026-01-01"}, partial=True) == {"end_date": "2026-01-01"}


@pytest.mark.parametrize("previous,target", list(product(sorted(STATUSES), repeat=2)))
@pytest.mark.req("REQ-EVT-B04")
def test_all_state_pairs(previous, target):
    allowed = previous == target or (previous, target) in {
        ("draft", "published"), ("draft", "cancelled"), ("published", "cancelled"),
    }
    if allowed:
        validate_transition(previous, target)
    else:
        with pytest.raises(ApiError) as error:
            validate_transition(previous, target)
        assert error.value.code == "INVALID_STATUS_TRANSITION"

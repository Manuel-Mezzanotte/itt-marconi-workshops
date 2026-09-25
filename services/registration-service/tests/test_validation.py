"""REQ-REG-01, REQ-REG-03: input shapes, canonical references and read-only fields."""
from copy import deepcopy

import pytest

from app.errors import ApiError
from app.validation import validate_create, validate_patch


pytestmark = pytest.mark.req("REQ-REG-01")


def test_create_normalizes_without_mutating(payload):
    payload = {key: value.upper() for key, value in payload.items()}
    before = deepcopy(payload)
    assert validate_create(payload) == {key: value.lower() for key, value in payload.items()}
    assert payload == before


@pytest.mark.parametrize("field", ["user_id", "event_id"])
@pytest.mark.parametrize("value", ["", "bad", "00000000000040008000000000000001", [], None, 1])
def test_uuid_validation(payload, field, value):
    with pytest.raises(ApiError) as exc:
        validate_create({**payload, field: value})
    assert exc.value.status == 422 and exc.value.code == "VALIDATION_ERROR"


@pytest.mark.parametrize("data", [None, [], False, 1, "text", {}, {"user_id": "missing"}])
def test_invalid_create_shape(data):
    with pytest.raises(ApiError):
        validate_create(data)


@pytest.mark.parametrize("field", ["id", "amount", "status", "created_at", "updated_at", "extra"])
def test_extra_and_readonly(payload, field):
    with pytest.raises(ApiError):
        validate_create({**payload, field: "client"})


@pytest.mark.parametrize("data", [None, [], False, {}, {"status": None}, {"status": []},
                                  {"status": {}}, {"status": "other"}, {"status": "cancelled", "amount": 1}])
def test_patch_requires_status_only(data):
    with pytest.raises(ApiError):
        validate_patch(data)


@pytest.mark.parametrize("status", ["confirmed", "cancelled"])
def test_patch_valid_status(status):
    assert validate_patch({"status": status}) == status

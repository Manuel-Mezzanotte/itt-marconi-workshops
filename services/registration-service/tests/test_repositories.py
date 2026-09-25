"""REQ-REG-B04, REQ-REG-B05, REQ-REG-B07, REQ-REG-02, REQ-REG-04."""
from concurrent.futures import ThreadPoolExecutor
import json
from uuid import uuid4

import pytest

from app.errors import ApiError
from app.repositories import get_repository


pytestmark = pytest.mark.req("REQ-REG-04")
EVENT = "00000000-0000-4000-8000-000000000001"
USER = "00000000-0000-4000-8000-000000000002"
NOW = "2026-01-01T00:00:00.000000Z"
LATER = "2026-01-02T00:00:00.000000Z"


def record(**changes):
    return {"id": str(uuid4()), "user_id": USER, "event_id": EVENT, "amount": 149.0,
            "status": "confirmed", "created_at": NOW, "updated_at": NOW, **changes}


@pytest.fixture(params=["memory", "json", "sqlite"])
def storage(request, tmp_path):
    return get_repository(request.param, tmp_path), request.param, tmp_path


def test_missing_and_copies(storage):
    repo, _, _ = storage
    assert repo.get("missing") is None and repo.delete("missing") is False
    assert repo.update_status("missing", "cancelled", LATER) is None
    assert repo.list({}, 1, 20) == ([], 0) and repo.count_confirmed(EVENT) == 0
    original = record()
    created = repo.reserve(original, 2)
    original["amount"] = 1
    created["amount"] = 2
    repo.get(original["id"])["amount"] = 3
    repo.list({}, 1, 20)[0][0]["amount"] = 4
    assert repo.get(original["id"])["amount"] == 149.0
    with pytest.raises(ValueError):
        repo.reserve(record(id=original["id"], user_id=str(uuid4())), 10)
    assert repo.count_confirmed(EVENT) == 1


@pytest.mark.req("REQ-REG-B04")
@pytest.mark.req("REQ-REG-B05")
@pytest.mark.req("REQ-REG-B07")
def test_duplicate_before_full_and_cancel_allows_reregistration(storage):
    repo, _, _ = storage
    original = repo.reserve(record(), 1)
    with pytest.raises(ApiError) as duplicate:
        repo.reserve(record(), 1)
    assert duplicate.value.code == "ALREADY_REGISTERED"
    with pytest.raises(ApiError) as full:
        repo.reserve(record(user_id=str(uuid4())), 1)
    assert full.value.code == "EVENT_FULL"
    assert repo.get(original["id"]) == original
    assert repo.update_status(original["id"], "confirmed", LATER) == original
    cancelled = repo.update_status(original["id"], "cancelled", LATER)
    assert cancelled == {**original, "status": "cancelled", "updated_at": LATER}
    assert repo.update_status(original["id"], "cancelled", NOW) == cancelled
    with pytest.raises(ApiError) as transition:
        repo.update_status(original["id"], "confirmed", NOW)
    assert transition.value.code == "INVALID_STATUS_TRANSITION"
    assert repo.get(original["id"]) == cancelled and repo.count_confirmed(EVENT) == 0
    replacement = repo.reserve(record(), 1)
    assert replacement["id"] != original["id"] and repo.count_confirmed(EVENT) == 1
    assert repo.delete(replacement["id"]) is True
    assert repo.count_confirmed(EVENT) == 0
    assert repo.delete(original["id"]) is True
    assert repo.list({}, 1, 20) == ([], 0)


def test_filter_pagination_and_persistence(storage):
    repo, backend, directory = storage
    first = repo.reserve(record(id="a"), 10)
    second = repo.reserve(record(id="b", user_id=str(uuid4())), 10)
    other = repo.reserve(record(id="c", event_id=str(uuid4())), 10)
    cancelled = repo.update_status("b", "cancelled", LATER)
    assert repo.list({}, 1, 2) == ([first, cancelled], 3)
    assert repo.list({}, 2, 2) == ([other], 3)
    assert repo.list({}, 10**30, 20) == ([], 3)
    assert repo.list({"user_id": USER, "event_id": EVENT, "status": "confirmed"}, 1, 20) == ([first], 1)
    assert repo.list({"event_id": EVENT}, 1, 20) == ([first, cancelled], 2)
    assert repo.list({"user_id": second["user_id"], "status": "confirmed"}, 1, 20) == ([], 0)
    reopened = get_repository(backend, directory)
    assert reopened.get("a") == (None if backend == "memory" else first)
    if backend != "memory":
        assert reopened.get("b") == cancelled and reopened.count_confirmed(EVENT) == 1
        reopened.delete("a")
        assert get_repository(backend, directory).get("a") is None


@pytest.mark.parametrize("same_user", [False, True])
@pytest.mark.req("REQ-REG-B04")
@pytest.mark.req("REQ-REG-B05")
def test_concurrent_reservations_have_one_winner(storage, same_user):
    repo, _, _ = storage

    def reserve(number):
        try:
            repo.reserve(record(user_id=USER if same_user else str(uuid4())), 1)
            return "created"
        except ApiError as exc:
            return exc.code

    with ThreadPoolExecutor(max_workers=8) as pool:
        outcomes = list(pool.map(reserve, range(16)))
    assert outcomes.count("created") == 1
    assert outcomes.count("ALREADY_REGISTERED" if same_user else "EVENT_FULL") == 15
    assert repo.count_confirmed(EVENT) == 1


@pytest.mark.parametrize("same_user", [False, True])
@pytest.mark.req("REQ-REG-B04")
@pytest.mark.req("REQ-REG-B05")
def test_sqlite_distinct_instances_share_capacity_and_unique_constraint(tmp_path, same_user):
    repositories = [get_repository("sqlite", tmp_path) for _ in range(2)]

    def reserve(number):
        try:
            repositories[number % 2].reserve(record(user_id=USER if same_user else str(uuid4())), 1)
            return "created"
        except ApiError as exc:
            return exc.code

    with ThreadPoolExecutor(max_workers=8) as pool:
        outcomes = list(pool.map(reserve, range(16)))
    assert outcomes.count("created") == 1
    assert outcomes.count("ALREADY_REGISTERED" if same_user else "EVENT_FULL") == 15


def test_json_failed_write_keeps_record(tmp_path, monkeypatch):
    repo = get_repository("json", tmp_path)
    original = repo.reserve(record(), 10)
    before = (tmp_path / "registrations.json").read_bytes()

    def fail(*args):
        raise OSError("replace failed")

    monkeypatch.setattr("app.repositories.json_repo.os.replace", fail)
    with pytest.raises(OSError):
        repo.update_status(original["id"], "cancelled", LATER)
    with pytest.raises(OSError):
        repo.reserve(record(user_id=str(uuid4())), 10)
    assert (tmp_path / "registrations.json").read_bytes() == before
    assert list(tmp_path.glob("*.tmp")) == []


def test_corrupt_json_is_not_overwritten(tmp_path):
    path = tmp_path / "registrations.json"
    path.write_text("{broken")
    with pytest.raises(json.JSONDecodeError):
        get_repository("json", tmp_path).reserve(record(), 10)
    assert path.read_text() == "{broken"


def test_unknown_backend(tmp_path):
    with pytest.raises(ValueError):
        get_repository("postgres", tmp_path)

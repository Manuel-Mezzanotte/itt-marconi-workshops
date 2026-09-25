"""REQ-EVT-02, REQ-EVT-03, REQ-EVT-05, REQ-EVT-B06."""
from concurrent.futures import ThreadPoolExecutor
import json

import pytest

from app.repositories import get_repository


pytestmark = pytest.mark.req("REQ-EVT-05")


@pytest.fixture(params=["memory", "json", "sqlite"])
def storage(request, tmp_path):
    return get_repository(request.param, tmp_path), request.param, tmp_path


def record(identifier="a", **changes):
    return {
        "id": identifier, "title": "Conference", "description": None,
        "organizer_id": "00000000-0000-4000-8000-000000000001",
        "venue": "Auditorium", "city": "Trento", "start_date": "2026-11-10",
        "end_date": "2026-11-11", "capacity": 100, "price": 149.0,
        "status": "draft", "created_at": "2026-01-01T00:00:00.000000Z",
        "updated_at": "2026-01-01T00:00:00.000000Z", **changes,
    }


def test_crud_and_missing(storage):
    repo, _, _ = storage
    assert repo.get("missing") is None
    assert repo.update("missing", lambda item: item) is None
    assert repo.delete("missing") is False
    original = record()
    assert repo.create(original) == original
    updated = repo.update("a", lambda item: {**item, "city": "Roma"})
    assert updated["city"] == "Roma" and repo.get("a") == updated
    assert repo.delete("a") is True
    assert repo.delete("a") is False and repo.list({}, 1, 20) == ([], 0)


def test_returns_copies_and_duplicate_id_preserves_original(storage):
    repo, _, _ = storage
    original = record()
    created = repo.create(original)
    original["title"] = "Changed input"
    created["title"] = "Changed output"
    repo.get("a")["title"] = "Changed get"
    repo.list({}, 1, 20)[0][0]["title"] = "Changed list"
    updated = repo.update("a", lambda item: {**item, "city": "Roma"})
    updated["city"] = "Changed output"
    assert repo.get("a") == record(city="Roma")
    with pytest.raises(ValueError):
        repo.create(record(title="Replacement"))
    assert repo.get("a") == record(city="Roma")


def test_filter_sort_pagination(storage):
    repo, _, _ = storage
    for item in [record("c", status="published"), record("a"), record("b", city="Roma")]:
        repo.create(item)
    assert repo.list({}, 1, 2) == ([record("a"), record("b", city="Roma")], 3)
    assert repo.list({}, 2, 2) == ([record("c", status="published")], 3)
    assert repo.list({}, 10**30, 20) == ([], 3)
    assert repo.list({"city": "Trento", "status": "published"}, 1, 20) == (
        [record("c", status="published")], 1,
    )
    assert repo.list({"city": "trento"}, 1, 20) == ([], 0)
    assert repo.list({"city": ""}, 1, 20) == ([], 0)


def test_persistence_and_memory_isolation(storage):
    repo, backend, directory = storage
    original = record()
    repo.create(original)
    reopened = get_repository(backend, directory)
    assert reopened.get("a") == (None if backend == "memory" else original)
    repo.update("a", lambda item: {**item, "city": "Roma"})
    if backend != "memory":
        assert get_repository(backend, directory).get("a")["city"] == "Roma"
        repo.delete("a")
        assert get_repository(backend, directory).get("a") is None


def test_transform_failure_rolls_back(storage):
    repo, _, _ = storage
    original = record()
    repo.create(original)

    def fail(item):
        item["city"] = "Mutated before exception"
        raise ValueError("invalid transition")

    with pytest.raises(ValueError):
        repo.update("a", fail)
    assert repo.get("a") == original
    assert repo.update("a", lambda item: {**item, "city": "Roma"})["city"] == "Roma"


def test_concurrent_updates_do_not_lose_changes(storage):
    repo, _, _ = storage
    repo.create(record(capacity=1))
    with ThreadPoolExecutor(max_workers=6) as pool:
        list(pool.map(lambda _: repo.update("a", lambda item: {
            **item, "capacity": item["capacity"] + 1,
        }), range(24)))
    assert repo.get("a")["capacity"] == 25


def test_json_failed_replace_keeps_file(tmp_path, monkeypatch):
    repo = get_repository("json", tmp_path)
    repo.create(record())
    before = (tmp_path / "events.json").read_bytes()

    def fail(*args):
        raise OSError("replace failed")

    monkeypatch.setattr("app.repositories.json_repo.os.replace", fail)
    with pytest.raises(OSError):
        repo.update("a", lambda item: {**item, "city": "Roma"})
    assert (tmp_path / "events.json").read_bytes() == before
    assert list(tmp_path.glob("*.tmp")) == []


def test_json_corruption_is_not_silently_overwritten(tmp_path):
    path = tmp_path / "events.json"
    path.write_text("{broken")
    repo = get_repository("json", tmp_path)
    with pytest.raises(json.JSONDecodeError):
        repo.create(record())
    assert path.read_text() == "{broken"


def test_unknown_backend(tmp_path):
    with pytest.raises(ValueError):
        get_repository("postgres", tmp_path)

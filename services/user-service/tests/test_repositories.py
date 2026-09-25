"""Parametrised repository tests for user-service.

Tests run against all three backends: memory, json, sqlite.
File-based backends use pytest's tmp_path so no real data directory is touched.

Traceability:
  REQ-USR-B01   — email uniqueness (create & update)
  REQ-USR-03    — pagination
  REQ-USR-B03   — filters (role, email, combined)
  REQ-USR-09    — backend configuration & persistence
  REQ-USR-12    — unit test coverage
"""
from __future__ import annotations

import copy
import threading
import time
from pathlib import Path
from typing import Any

import pytest

from app.errors import EmailAlreadyExists
from app.repositories import get_repository, UserRepository


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

def _make_repo(backend: str, tmp_path: Path) -> UserRepository:
    return get_repository(backend, tmp_path / backend)


@pytest.fixture(params=["memory", "json", "sqlite"])
def repo(request, tmp_path):
    """A fresh repository instance for each backend."""
    return _make_repo(request.param, tmp_path)


# ---------------------------------------------------------------------------
# Sample user builder
# ---------------------------------------------------------------------------

def _user(
    uid: str = "user-001",
    email: str = "alice@example.com",
    first_name: str = "Alice",
    last_name: str = "Smith",
    role: str = "attendee",
    company: str | None = None,
    created_at: str = "2026-01-01T00:00:00Z",
    updated_at: str = "2026-01-01T00:00:00Z",
) -> dict[str, Any]:
    return {
        "id": uid,
        "first_name": first_name,
        "last_name": last_name,
        "email": email,
        "company": company,
        "role": role,
        "created_at": created_at,
        "updated_at": updated_at,
    }


# ---------------------------------------------------------------------------
# CRUD — basic operations
# ---------------------------------------------------------------------------

class TestCreateAndGet:
    """REQ-USR-B01, REQ-USR-09"""

    def test_create_returns_copy(self, repo):
        """create() returns a copy, not a reference to the stored record."""
        u = _user()
        result = repo.create(u)
        assert result == u
        result["first_name"] = "MUTATED"
        # The stored record must be unaffected
        fetched = repo.get(u["id"])
        assert fetched["first_name"] == "Alice"

    def test_get_existing(self, repo):
        """get() returns the stored record (REQ-USR-09)."""
        u = _user()
        repo.create(u)
        fetched = repo.get(u["id"])
        assert fetched is not None
        assert fetched["id"] == u["id"]
        assert fetched["email"] == u["email"]

    def test_get_nonexistent_returns_none(self, repo):
        assert repo.get("no-such-id") is None

    def test_get_returns_copy(self, repo):
        """Mutations to the returned dict do not affect stored data."""
        u = _user()
        repo.create(u)
        result1 = repo.get(u["id"])
        result1["first_name"] = "MUTATED"
        result2 = repo.get(u["id"])
        assert result2["first_name"] == "Alice"

    def test_get_by_email_existing(self, repo):
        """get_by_email() performs case-insensitive lookup (REQ-USR-B01)."""
        u = _user(email="alice@example.com")
        repo.create(u)
        assert repo.get_by_email("alice@example.com") is not None
        assert repo.get_by_email("ALICE@EXAMPLE.COM") is not None

    def test_get_by_email_nonexistent_returns_none(self, repo):
        assert repo.get_by_email("no@example.com") is None


class TestDelete:
    """REQ-USR-09"""

    def test_delete_existing_returns_true(self, repo):
        u = _user()
        repo.create(u)
        assert repo.delete(u["id"]) is True
        assert repo.get(u["id"]) is None

    def test_delete_nonexistent_returns_false(self, repo):
        assert repo.delete("ghost-id") is False

    def test_second_delete_returns_false(self, repo):
        u = _user()
        repo.create(u)
        repo.delete(u["id"])
        assert repo.delete(u["id"]) is False


class TestUpdate:
    """REQ-USR-B01, REQ-USR-09"""

    def test_update_existing_record(self, repo):
        u = _user()
        repo.create(u)
        modified = copy.deepcopy(u)
        modified["first_name"] = "Bob"
        modified["updated_at"] = "2026-06-01T00:00:00Z"
        result = repo.update(u["id"], modified)
        assert result is not None
        assert result["first_name"] == "Bob"
        # Verify persistence
        fetched = repo.get(u["id"])
        assert fetched["first_name"] == "Bob"

    def test_update_nonexistent_returns_none(self, repo):
        u = _user()
        assert repo.update("ghost-id", u) is None

    def test_update_returns_copy(self, repo):
        u = _user()
        repo.create(u)
        modified = copy.deepcopy(u)
        result = repo.update(u["id"], modified)
        result["first_name"] = "MUTATED"
        fetched = repo.get(u["id"])
        assert fetched["first_name"] == "Alice"

    def test_update_own_email_allowed(self, repo):
        """REQ-USR-B01.4: updating with the same email must succeed."""
        u = _user(email="alice@example.com")
        repo.create(u)
        modified = copy.deepcopy(u)
        modified["first_name"] = "Updated"
        result = repo.update(u["id"], modified)
        assert result is not None
        assert result["email"] == "alice@example.com"

    def test_update_own_email_case_insensitive(self, repo):
        """Updating with the same email in different case must succeed."""
        u = _user(email="alice@example.com")
        repo.create(u)
        modified = copy.deepcopy(u)
        modified["email"] = "ALICE@EXAMPLE.COM"
        # Should NOT raise EmailAlreadyExists
        result = repo.update(u["id"], modified)
        assert result is not None


# ---------------------------------------------------------------------------
# Email uniqueness
# ---------------------------------------------------------------------------

class TestEmailUniqueness:
    """REQ-USR-B01: uniqueness enforced atomically."""

    def test_create_duplicate_email_raises(self, repo):
        """Two users with the same email → EmailAlreadyExists on second create."""
        repo.create(_user(uid="u1", email="alice@example.com"))
        with pytest.raises(EmailAlreadyExists):
            repo.create(_user(uid="u2", email="alice@example.com"))

    def test_create_duplicate_email_case_insensitive(self, repo):
        repo.create(_user(uid="u1", email="alice@example.com"))
        with pytest.raises(EmailAlreadyExists):
            repo.create(_user(uid="u2", email="ALICE@EXAMPLE.COM"))

    def test_duplicate_create_does_not_mutate_store(self, repo):
        """A failed create must leave the store unchanged."""
        repo.create(_user(uid="u1", email="alice@example.com"))
        try:
            repo.create(_user(uid="u2", email="alice@example.com"))
        except EmailAlreadyExists:
            pass
        # Only the original user should exist
        items, total = repo.list({}, 1, 100)
        assert total == 1
        assert items[0]["id"] == "u1"

    def test_update_email_conflict_raises(self, repo):
        """REQ-USR-B01.2: updating to another user's email → EmailAlreadyExists."""
        repo.create(_user(uid="u1", email="alice@example.com"))
        repo.create(_user(uid="u2", email="bob@example.com"))
        conflict = copy.deepcopy(repo.get("u2"))
        conflict["email"] = "alice@example.com"
        with pytest.raises(EmailAlreadyExists):
            repo.update("u2", conflict)

    def test_update_email_conflict_does_not_mutate(self, repo):
        """REQ-USR-B01: a failed update must not change any data."""
        repo.create(_user(uid="u1", email="alice@example.com"))
        u2 = _user(uid="u2", email="bob@example.com", first_name="Bob")
        repo.create(u2)
        conflict = copy.deepcopy(u2)
        conflict["email"] = "alice@example.com"
        conflict["first_name"] = "SHOULD_NOT_SAVE"
        try:
            repo.update("u2", conflict)
        except EmailAlreadyExists:
            pass
        fetched = repo.get("u2")
        assert fetched["email"] == "bob@example.com"
        assert fetched["first_name"] == "Bob"

    def test_email_freed_after_delete(self, repo):
        """After deleting a user the email can be reused."""
        u = _user(uid="u1", email="alice@example.com")
        repo.create(u)
        repo.delete("u1")
        repo.create(_user(uid="u2", email="alice@example.com"))
        assert repo.get("u2") is not None


# ---------------------------------------------------------------------------
# List, pagination and filters
# ---------------------------------------------------------------------------

class TestList:
    """REQ-USR-03, REQ-USR-B03"""

    def _populate(self, repo, n: int = 5):
        users = []
        for i in range(n):
            u = _user(
                uid=f"u{i:03d}",
                email=f"user{i:03d}@example.com",
                first_name=f"User{i}",
                last_name="Test",
                role="attendee" if i % 2 == 0 else "speaker",
                created_at=f"2026-01-{i+1:02d}T00:00:00Z",
                updated_at=f"2026-01-{i+1:02d}T00:00:00Z",
            )
            repo.create(u)
            users.append(u)
        return users

    def test_list_empty_repository(self, repo):
        items, total = repo.list({}, 1, 20)
        assert items == []
        assert total == 0

    def test_list_all_default_page(self, repo):
        self._populate(repo, 5)
        items, total = repo.list({}, 1, 20)
        assert total == 5
        assert len(items) == 5

    def test_list_pagination_page1(self, repo):
        self._populate(repo, 5)
        items, total = repo.list({}, 1, 3)
        assert total == 5
        assert len(items) == 3

    def test_list_pagination_page2(self, repo):
        self._populate(repo, 5)
        items, total = repo.list({}, 2, 3)
        assert total == 5
        assert len(items) == 2

    def test_list_page_beyond_end_returns_empty(self, repo):
        """REQ-USR-03: a page past the last record returns an empty list."""
        self._populate(repo, 3)
        items, total = repo.list({}, 99, 20)
        assert items == []
        assert total == 3

    def test_list_very_large_offset(self, repo):
        """Huge page number must not raise an error (SQLite offset guard)."""
        self._populate(repo, 3)
        items, total = repo.list({}, 10**30, 20)
        assert items == []
        assert total == 3

    def test_list_stable_order(self, repo):
        """Items must be ordered by (created_at, id) ascending."""
        self._populate(repo, 5)
        items, _ = repo.list({}, 1, 100)
        for a, b in zip(items, items[1:]):
            assert (a["created_at"], a["id"]) <= (b["created_at"], b["id"])

    def test_list_consecutive_pages_cover_all(self, repo):
        """Pages must partition the full result set without gaps or overlaps."""
        self._populate(repo, 5)
        page1, total = repo.list({}, 1, 3)
        page2, _ = repo.list({}, 2, 3)
        all_ids = [r["id"] for r in page1] + [r["id"] for r in page2]
        assert len(all_ids) == total
        assert len(set(all_ids)) == total

    def test_filter_by_role(self, repo):
        """REQ-USR-B03: role filter restricts results and total."""
        self._populate(repo, 5)
        items, total = repo.list({"role": "attendee"}, 1, 100)
        assert all(u["role"] == "attendee" for u in items)
        assert total == len(items)

    def test_filter_by_email_exact(self, repo):
        """REQ-USR-B03: email filter is an exact match on normalised email."""
        self._populate(repo, 5)
        items, total = repo.list({"email": "user002@example.com"}, 1, 100)
        assert total == 1
        assert items[0]["email"] == "user002@example.com"

    def test_filter_by_email_case_insensitive(self, repo):
        """REQ-USR-B03: email filter is case-insensitive."""
        self._populate(repo, 3)
        items, total = repo.list({"email": "USER000@EXAMPLE.COM"}, 1, 100)
        assert total == 1

    def test_filter_combined_role_and_email(self, repo):
        """REQ-USR-B03.4: role and email filters combine with AND."""
        self._populate(repo, 5)
        items, total = repo.list({"role": "attendee", "email": "user002@example.com"}, 1, 100)
        assert total == 1
        assert items[0]["role"] == "attendee"

    def test_filter_combined_no_match(self, repo):
        """Combined filters that produce no match return empty list."""
        self._populate(repo, 5)
        # user000 is attendee, user001 is speaker
        items, total = repo.list({"role": "speaker", "email": "user000@example.com"}, 1, 100)
        assert total == 0
        assert items == []

    def test_total_reflects_filter(self, repo):
        """REQ-USR-B03.1: total counts only filtered records."""
        self._populate(repo, 6)  # 3 attendee, 3 speaker
        _, total_attendees = repo.list({"role": "attendee"}, 1, 100)
        _, total_all = repo.list({}, 1, 100)
        assert total_attendees < total_all


# ---------------------------------------------------------------------------
# Persistence: JSON and SQLite re-open
# ---------------------------------------------------------------------------

class TestPersistence:
    """REQ-USR-09.7: data survives across repository instances."""

    @pytest.mark.parametrize("backend", ["json", "sqlite"])
    def test_data_persists_across_instances(self, backend, tmp_path):
        data_dir = tmp_path / backend
        repo1 = get_repository(backend, data_dir)
        u = _user()
        repo1.create(u)

        # Open a second instance pointing to the same directory
        repo2 = get_repository(backend, data_dir)
        fetched = repo2.get(u["id"])
        assert fetched is not None
        assert fetched["id"] == u["id"]

    @pytest.mark.parametrize("backend", ["json", "sqlite"])
    def test_delete_persists_across_instances(self, backend, tmp_path):
        data_dir = tmp_path / backend
        repo1 = get_repository(backend, data_dir)
        u = _user()
        repo1.create(u)
        repo1.delete(u["id"])

        repo2 = get_repository(backend, data_dir)
        assert repo2.get(u["id"]) is None


# ---------------------------------------------------------------------------
# Memory isolation
# ---------------------------------------------------------------------------

class TestMemoryIsolation:
    """REQ-USR-09.8: separate memory instances are independent."""

    def test_two_memory_instances_are_isolated(self, tmp_path):
        repo1 = get_repository("memory", tmp_path)
        repo2 = get_repository("memory", tmp_path)
        u = _user()
        repo1.create(u)
        assert repo2.get(u["id"]) is None

    def test_memory_starts_empty(self, tmp_path):
        repo = get_repository("memory", tmp_path)
        _, total = repo.list({}, 1, 100)
        assert total == 0


# ---------------------------------------------------------------------------
# JSON atomic write: failure does not corrupt existing file
# ---------------------------------------------------------------------------

class TestJsonAtomicWrite:
    """Verify that an error during write leaves the file intact."""

    def test_failed_write_does_not_corrupt_file(self, tmp_path, monkeypatch):
        from app.repositories.json_repo import JsonRepository
        import os

        data_dir = tmp_path / "json_atomic"
        repo = JsonRepository(data_dir)
        u = _user()
        repo.create(u)

        # Make os.replace raise an error to simulate a failure mid-write
        original_replace = os.replace

        def broken_replace(src, dst):
            # Remove the temp file so it does not litter, then raise
            try:
                os.unlink(src)
            except OSError:
                pass
            raise OSError("Simulated disk error")

        monkeypatch.setattr(os, "replace", broken_replace)

        u2 = _user(uid="u2", email="bob@example.com")
        with pytest.raises(OSError):
            repo.create(u2)

        # Restore and verify original data intact
        monkeypatch.setattr(os, "replace", original_replace)
        repo2 = JsonRepository(data_dir)
        items, total = repo2.list({}, 1, 100)
        assert total == 1
        assert items[0]["id"] == u["id"]


# ---------------------------------------------------------------------------
# Concurrent writes: same email race
# ---------------------------------------------------------------------------

class TestConcurrentEmail:
    """REQ-USR-B01: at most one thread can create a user with a given email."""

    @pytest.mark.parametrize("backend", ["memory", "json", "sqlite"])
    def test_concurrent_same_email_only_one_succeeds(self, backend, tmp_path):
        """Start N threads simultaneously; only one should succeed."""
        repo = get_repository(backend, tmp_path / backend)
        n_threads = 10
        results: list[Exception | dict] = [None] * n_threads
        barrier = threading.Barrier(n_threads)

        def worker(idx):
            barrier.wait()
            try:
                u = _user(
                    uid=f"concurrent-{idx:03d}",
                    email="shared@example.com",
                )
                results[idx] = repo.create(u)
            except EmailAlreadyExists as exc:
                results[idx] = exc

        threads = [threading.Thread(target=worker, args=(i,)) for i in range(n_threads)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        successes = [r for r in results if isinstance(r, dict)]
        failures = [r for r in results if isinstance(r, EmailAlreadyExists)]
        assert len(successes) == 1, f"Expected 1 success, got {len(successes)}"
        assert len(failures) == n_threads - 1

    @pytest.mark.parametrize("backend", ["memory", "json", "sqlite"])
    def test_concurrent_update_same_email_only_one_succeeds(self, backend, tmp_path):
        """Two users racing to take the same email: exactly one update wins."""
        repo = get_repository(backend, tmp_path / backend)
        u1 = _user(uid="u1", email="user1@example.com")
        u2 = _user(uid="u2", email="user2@example.com")
        repo.create(u1)
        repo.create(u2)

        results: list[Exception | dict | None] = [None, None]
        barrier = threading.Barrier(2)

        def update_worker(idx, user_id, new_email):
            barrier.wait()
            current = repo.get(user_id)
            updated = copy.deepcopy(current)
            updated["email"] = new_email
            try:
                results[idx] = repo.update(user_id, updated)
            except EmailAlreadyExists as exc:
                results[idx] = exc

        # Both try to steal "shared@example.com"
        t0 = threading.Thread(target=update_worker, args=(0, "u1", "shared@example.com"))
        t1 = threading.Thread(target=update_worker, args=(1, "u2", "shared@example.com"))
        t0.start()
        t1.start()
        t0.join()
        t1.join()

        successes = [r for r in results if isinstance(r, dict)]
        failures = [r for r in results if isinstance(r, EmailAlreadyExists)]
        assert len(successes) == 1, f"Expected exactly 1 success, got {len(successes)}"
        assert len(failures) == 1, f"Expected exactly 1 EmailAlreadyExists, got {len(failures)}"

        # Exactly one record holds shared@example.com; the loser kept its old email
        winner_idx = next(i for i, r in enumerate(results) if isinstance(r, dict))
        loser_idx = 1 - winner_idx
        winner_id = "u1" if winner_idx == 0 else "u2"
        loser_id  = "u2" if winner_idx == 0 else "u1"
        loser_original_email = "user1@example.com" if loser_id == "u1" else "user2@example.com"

        winner_record = repo.get(winner_id)
        loser_record  = repo.get(loser_id)
        assert winner_record["email"].lower() == "shared@example.com"
        assert loser_record["email"].lower() == loser_original_email

        # Confirm only one record holds shared@example.com
        items, _ = repo.list({}, 1, 100)
        shared_holders = [r for r in items if r["email"].lower() == "shared@example.com"]
        assert len(shared_holders) == 1


# ---------------------------------------------------------------------------
# list() returns copies
# ---------------------------------------------------------------------------

class TestListReturnsCopies:
    """Mutations to items returned by list() must not affect stored data."""

    @pytest.fixture(params=["memory", "json", "sqlite"])
    def repo_with_data(self, request, tmp_path):
        repo = get_repository(request.param, tmp_path / request.param)
        repo.create(_user(uid="u1", email="alice@example.com", first_name="Alice"))
        return repo

    def test_list_item_mutation_does_not_affect_store(self, repo_with_data):
        """REQ-USR-09: list() items are copies; mutations are not persisted."""
        repo = repo_with_data
        items, _ = repo.list({}, 1, 100)
        assert len(items) == 1
        items[0]["first_name"] = "MUTATED"
        # Re-fetch via get: stored record must be unchanged
        stored = repo.get("u1")
        assert stored["first_name"] == "Alice"

    def test_list_twice_returns_independent_copies(self, repo_with_data):
        """Two consecutive list() calls return independent dicts."""
        repo = repo_with_data
        items1, _ = repo.list({}, 1, 100)
        items2, _ = repo.list({}, 1, 100)
        items1[0]["first_name"] = "MUTATED"
        assert items2[0]["first_name"] == "Alice"


# ---------------------------------------------------------------------------
# Stable ordering with equal created_at, inserted in reverse id order
# ---------------------------------------------------------------------------

class TestListOrderSameCreatedAt:
    """When created_at is identical the secondary sort key (id) must hold."""

    @pytest.fixture(params=["memory", "json", "sqlite"])
    def repo_reversed(self, request, tmp_path):
        """Insert users with the same created_at but ids in reverse order."""
        repo = get_repository(request.param, tmp_path / request.param)
        # Insert in reverse id order so an unstable sort would expose the issue
        for i in range(4, -1, -1):
            repo.create(_user(
                uid=f"u{i:03d}",
                email=f"u{i:03d}@example.com",
                created_at="2026-06-01T00:00:00Z",
                updated_at="2026-06-01T00:00:00Z",
            ))
        return repo

    def test_same_created_at_sorted_by_id(self, repo_reversed):
        """REQ-USR-03: (created_at, id) ordering is stable when created_at ties."""
        items, total = repo_reversed.list({}, 1, 100)
        assert total == 5
        ids = [r["id"] for r in items]
        assert ids == sorted(ids), f"Expected sorted ids, got {ids}"

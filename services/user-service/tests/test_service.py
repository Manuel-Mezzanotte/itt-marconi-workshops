"""UserService tests for create_user [T-03].

REQ-USR-B02, REQ-USR-10, REQ-USR-11, REQ-USR-12
"""
from __future__ import annotations

import re
from datetime import datetime, timezone
from pathlib import Path
from uuid import UUID

import pytest

from app.errors import EmailAlreadyExists, ValidationError
from app.repositories import get_repository
from app.service import UserService


@pytest.fixture(params=["memory", "json", "sqlite"])
def service(request, tmp_path):
    """UserService with each backend."""
    repo = get_repository(request.param, tmp_path / request.param)
    return UserService(repo)


class TestUserServiceCreate:
    """REQ-USR-B02, REQ-USR-10: create_user behavior."""

    def test_create_generates_uuid(self, service):
        """id is a valid UUID v4."""
        data = {
            "first_name": "Alice",
            "last_name": "Smith",
            "email": "alice@example.com",
        }
        user = service.create_user(data)
        # Verify it's a valid UUID
        try:
            UUID(user["id"])
        except ValueError:
            pytest.fail("id is not a valid UUID")

    def test_create_generates_timestamp_utc_with_z(self, service):
        """created_at and updated_at are ISO 8601 UTC with Z suffix."""
        data = {
            "first_name": "Alice",
            "last_name": "Smith",
            "email": "alice@example.com",
        }
        user = service.create_user(data)
        # Pattern: YYYY-MM-DDTHH:MM:SS.SSSZ
        iso_pattern = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3}Z$")
        assert iso_pattern.match(user["created_at"]), f"Bad format: {user['created_at']}"
        assert iso_pattern.match(user["updated_at"]), f"Bad format: {user['updated_at']}"
        # Verify they're actually UTC
        now = datetime.now(timezone.utc)
        created = datetime.fromisoformat(user["created_at"].replace("Z", "+00:00"))
        assert abs((now - created).total_seconds()) < 5  # Within 5 seconds

    def test_create_timestamp_equal(self, service):
        """created_at == updated_at for new record."""
        data = {
            "first_name": "Alice",
            "last_name": "Smith",
            "email": "alice@example.com",
        }
        user = service.create_user(data)
        assert user["created_at"] == user["updated_at"]

    def test_create_with_defaults(self, service):
        """role defaults to 'attendee', company to null."""
        data = {
            "first_name": "Alice",
            "last_name": "Smith",
            "email": "alice@example.com",
        }
        user = service.create_user(data)
        assert user["role"] == "attendee"
        assert user["company"] is None

    def test_create_email_normalized(self, service):
        """Email stored as lowercase."""
        data = {
            "first_name": "Alice",
            "last_name": "Smith",
            "email": "Alice.Smith@EXAMPLE.COM",
        }
        user = service.create_user(data)
        assert user["email"] == "alice.smith@example.com"

    def test_create_preserves_required_fields(self, service):
        """All required fields are stored correctly."""
        data = {
            "first_name": "Alice",
            "last_name": "Smith",
            "email": "alice@example.com",
            "company": "TechCorp",
            "role": "speaker",
        }
        user = service.create_user(data)
        assert user["first_name"] == "Alice"
        assert user["last_name"] == "Smith"
        assert user["email"] == "alice@example.com"
        assert user["company"] == "TechCorp"
        assert user["role"] == "speaker"

    def test_create_validation_error_propagates(self, service):
        """ValidationError from validate_user_create is raised."""
        data = {
            "first_name": "Alice",
            # Missing last_name
            "email": "alice@example.com",
        }
        with pytest.raises(ValidationError):
            service.create_user(data)

    def test_create_email_already_exists(self, service):
        """Duplicate email raises EmailAlreadyExists."""
        data1 = {
            "first_name": "Alice",
            "last_name": "Smith",
            "email": "alice@example.com",
        }
        service.create_user(data1)
        
        data2 = {
            "first_name": "Bob",
            "last_name": "Jones",
            "email": "alice@example.com",  # Same email, case-insensitive
        }
        with pytest.raises(EmailAlreadyExists):
            service.create_user(data2)

    def test_create_email_case_insensitive_duplicate(self, service):
        """Email duplicate check is case-insensitive."""
        data1 = {
            "first_name": "Alice",
            "last_name": "Smith",
            "email": "alice@example.com",
        }
        service.create_user(data1)
        
        data2 = {
            "first_name": "Bob",
            "last_name": "Jones",
            "email": "ALICE@EXAMPLE.COM",
        }
        with pytest.raises(EmailAlreadyExists):
            service.create_user(data2)

    def test_create_different_emails_allowed(self, service):
        """Different emails are allowed."""
        data1 = {
            "first_name": "Alice",
            "last_name": "Smith",
            "email": "alice@example.com",
        }
        user1 = service.create_user(data1)
        
        data2 = {
            "first_name": "Bob",
            "last_name": "Jones",
            "email": "bob@example.com",
        }
        user2 = service.create_user(data2)
        
        assert user1["id"] != user2["id"]
        assert user1["email"] != user2["email"]

    def test_create_input_not_modified(self, service):
        """Input dict is never modified by create_user."""
        data = {
            "first_name": "Alice",
            "last_name": "Smith",
            "email": "ALICE@EXAMPLE.COM",
        }
        original = dict(data)
        service.create_user(data)
        assert data == original

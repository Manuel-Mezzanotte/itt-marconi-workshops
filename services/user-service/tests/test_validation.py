"""Validation tests for user-service [T-03].

REQ-USR-01, REQ-USR-B02, REQ-USR-10, REQ-USR-11
"""
from __future__ import annotations

import pytest

from app.errors import ValidationError
from app.validation import validate_user_create


class TestUserCreateValidation:
    """REQ-USR-01, REQ-USR-B02: UserCreate payload validation."""

    # Markers and tests for Issue #1 (read-only fields)
    @pytest.mark.parametrize("readonly_field", ["id", "created_at", "updated_at"])
    def test_readonly_field_rejected(self, readonly_field):
        """Issue #1: Read-only field in body raises 422."""
        data = {
            "first_name": "Alice",
            "last_name": "Smith",
            "email": "alice@example.com",
            readonly_field: "should-be-rejected",
        }
        with pytest.raises(ValidationError) as exc_info:
            validate_user_create(data)
        assert readonly_field in exc_info.value.details.get("fields", [])

    def test_valid_minimal(self):
        """Minimal valid payload with defaults."""
        data = {
            "first_name": "Alice",
            "last_name": "Smith",
            "email": "alice@example.com",
        }
        result = validate_user_create(data)
        assert result["first_name"] == "Alice"
        assert result["last_name"] == "Smith"
        assert result["email"] == "alice@example.com"
        assert result["role"] == "attendee"
        assert result["company"] is None

    def test_email_normalized_lowercase(self):
        """Email normalized to lowercase."""
        data = {
            "first_name": "Alice",
            "last_name": "Smith",
            "email": "Alice.Smith@EXAMPLE.COM",
        }
        result = validate_user_create(data)
        assert result["email"] == "alice.smith@example.com"

    def test_role_default(self):
        """role defaults to 'attendee' if not provided."""
        data = {
            "first_name": "Alice",
            "last_name": "Smith",
            "email": "alice@example.com",
        }
        result = validate_user_create(data)
        assert result["role"] == "attendee"

    def test_role_valid_values(self):
        """Valid role values: attendee, speaker, organizer."""
        for role in ["attendee", "speaker", "organizer"]:
            data = {
                "first_name": "Alice",
                "last_name": "Smith",
                "email": "alice@example.com",
                "role": role,
            }
            result = validate_user_create(data)
            assert result["role"] == role

    def test_role_invalid_value(self):
        """Invalid role raises 422."""
        data = {
            "first_name": "Alice",
            "last_name": "Smith",
            "email": "alice@example.com",
            "role": "invalid",
        }
        with pytest.raises(ValidationError) as exc_info:
            validate_user_create(data)
        assert "role" in exc_info.value.message.lower()
        assert exc_info.value.details.get("field") == "role"

    def test_not_a_dict(self):
        """Non-dict input raises 422."""
        for data in [None, "string", 123, [], {"a": 1, "b": 2}]:
            # Actually dicts don't raise for being dict-like
            pass
        # Test actual non-dict:
        with pytest.raises(ValidationError) as exc_info:
            validate_user_create(None)
        assert "object" in exc_info.value.message.lower()

    def test_extra_fields_rejected(self):
        """Extra fields raise 422."""
        data = {
            "first_name": "Alice",
            "last_name": "Smith",
            "email": "alice@example.com",
            "extra_field": "not-allowed",
        }
        with pytest.raises(ValidationError) as exc_info:
            validate_user_create(data)
        assert "Unknown" in exc_info.value.message
        assert "extra_field" in exc_info.value.details.get("fields", [])

    def test_missing_first_name(self):
        """Missing first_name raises 422."""
        data = {
            "last_name": "Smith",
            "email": "alice@example.com",
        }
        with pytest.raises(ValidationError) as exc_info:
            validate_user_create(data)
        assert "first_name" in exc_info.value.message.lower()

    def test_empty_first_name(self):
        """Empty first_name raises 422."""
        data = {
            "first_name": "",
            "last_name": "Smith",
            "email": "alice@example.com",
        }
        with pytest.raises(ValidationError) as exc_info:
            validate_user_create(data)
        assert "first_name" in exc_info.value.message.lower()

    def test_first_name_too_long(self):
        """first_name exceeding 50 chars raises 422."""
        data = {
            "first_name": "A" * 51,
            "last_name": "Smith",
            "email": "alice@example.com",
        }
        with pytest.raises(ValidationError) as exc_info:
            validate_user_create(data)
        assert "first_name" in exc_info.value.message.lower()
        assert "max" in str(exc_info.value.details).lower()

    def test_first_name_50_chars_ok(self):
        """first_name with 50 chars is valid."""
        data = {
            "first_name": "A" * 50,
            "last_name": "Smith",
            "email": "alice@example.com",
        }
        result = validate_user_create(data)
        assert len(result["first_name"]) == 50

    def test_first_name_wrong_type(self):
        """first_name must be string."""
        data = {
            "first_name": 123,
            "last_name": "Smith",
            "email": "alice@example.com",
        }
        with pytest.raises(ValidationError) as exc_info:
            validate_user_create(data)
        assert "first_name" in exc_info.value.message.lower()
        assert "string" in exc_info.value.message.lower()

    def test_email_invalid_format(self):
        """Invalid email format raises 422."""
        for bad_email in ["notanemail", "@example.com", "user@", "user@.com"]:
            data = {
                "first_name": "Alice",
                "last_name": "Smith",
                "email": bad_email,
            }
            with pytest.raises(ValidationError) as exc_info:
                validate_user_create(data)
            assert "email" in exc_info.value.message.lower()

    def test_company_optional_null(self):
        """company can be null."""
        data = {
            "first_name": "Alice",
            "last_name": "Smith",
            "email": "alice@example.com",
            "company": None,
        }
        result = validate_user_create(data)
        assert result["company"] is None

    def test_company_too_long(self):
        """company exceeding 100 chars raises 422."""
        data = {
            "first_name": "Alice",
            "last_name": "Smith",
            "email": "alice@example.com",
            "company": "C" * 101,
        }
        with pytest.raises(ValidationError) as exc_info:
            validate_user_create(data)
        assert "company" in exc_info.value.message.lower()

    def test_input_not_modified(self):
        """Input dict is never modified."""
        data = {
            "first_name": "Alice",
            "last_name": "Smith",
            "email": "ALICE@EXAMPLE.COM",
        }
        original = dict(data)
        validate_user_create(data)
        assert data == original

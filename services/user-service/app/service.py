"""Business logic for user-service.

UserService coordinates validation, repository operations, and domain
rules. It generates server-side identifiers and timestamps and applies
defaults and normalization.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from app.errors import EmailAlreadyExists
from app.repositories import UserRepository
from app.validation import validate_user_create


class UserService:
    """User domain service.

    Wraps a UserRepository and adds validation, defaults, normalization,
    and timestamp/id generation.
    """

    def __init__(self, repository: UserRepository) -> None:
        """Initialize with a UserRepository instance."""
        self._repo = repository

    def create_user(self, data: dict[str, Any]) -> dict[str, Any]:
        """Create a new user.

        Parameters
        ----------
        data:
            UserCreate payload (first_name, last_name, email; optional
            company, role).

        Returns
        -------
        Created user record with id, created_at, updated_at.

        Raises
        ------
        ValidationError
            If data fails validation.
        EmailAlreadyExists
            If another user with the same email exists.
        """
        # Validate and normalize input (never modifies caller's dict)
        validated = validate_user_create(data)

        # Generate server-side identifiers and timestamps
        now = datetime.now(timezone.utc)
        record = {
            "id": str(uuid.uuid4()),
            "first_name": validated["first_name"],
            "last_name": validated["last_name"],
            "email": validated["email"],
            "company": validated.get("company"),
            "role": validated["role"],
            "created_at": _format_timestamp(now),
            "updated_at": _format_timestamp(now),
        }

        # Persist to repository
        return self._repo.create(record)


def _format_timestamp(dt: datetime) -> str:
    """Format a datetime as ISO 8601 UTC with Z suffix and six-digit microseconds."""
    return dt.strftime("%Y-%m-%dT%H:%M:%S.%f") + "Z"

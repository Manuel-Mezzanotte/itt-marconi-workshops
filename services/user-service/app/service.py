"""Business logic for user-service.

UserService coordinates validation, repository operations, and domain
rules. It generates server-side identifiers and timestamps and applies
defaults and normalization.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from app.errors import UserNotFound
from app.repositories import UserRepository
from app.validation import validate_pagination, validate_role_filter, validate_user_create


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

    def get_user(self, user_id: str) -> dict[str, Any]:
        user = self._repo.get(user_id)
        if user is None:
            raise UserNotFound(user_id)
        return user

    def replace_user(self, user_id: str, data: dict[str, Any]) -> dict[str, Any]:
        current = self.get_user(user_id)
        validated = validate_user_create(data)
        replacement = {
            **validated,
            "id": current["id"],
            "created_at": current["created_at"],
            "updated_at": _format_timestamp(datetime.now(timezone.utc)),
        }
        updated = self._repo.update(user_id, replacement)
        if updated is None:
            raise UserNotFound(user_id)
        return updated

    def list_users(
        self,
        role: str | None = None,
        email: str | None = None,
        page: str | None = None,
        page_size: str | None = None,
    ) -> dict[str, Any]:
        page_number, size = validate_pagination(page, page_size)
        filters = {"role": validate_role_filter(role)}
        if email is not None:
            filters["email"] = email.lower()
        items, total = self._repo.list(filters, page_number, size)
        return {"items": items, "page": page_number, "page_size": size, "total": total}


def _format_timestamp(dt: datetime) -> str:
    """Format a datetime as ISO 8601 UTC with Z suffix and six-digit microseconds."""
    return dt.strftime("%Y-%m-%dT%H:%M:%S.%f") + "Z"

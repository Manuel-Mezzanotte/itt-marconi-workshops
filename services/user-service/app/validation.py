"""Validation helpers for user-service.

Defines schemas for UserCreate and UserUpdate, plus query parameter
validation for list endpoints.

All validation functions return a new dict (never modify the input) or
raise ValidationError with a details dict explaining the issue.
"""
from __future__ import annotations

import re
from copy import deepcopy
from typing import Any

from app.errors import ValidationError


# Read-only fields that must not appear in any write operation.
_READ_ONLY_FIELDS = frozenset({"id", "created_at", "updated_at"})

# Allowed fields for each schema.
_USER_CREATE_FIELDS = frozenset({"first_name", "last_name", "email", "company", "role"})
_USER_UPDATE_FIELDS = frozenset({"first_name", "last_name", "email", "company", "role"})

# Valid role values.
_VALID_ROLES = frozenset({"attendee", "speaker", "organizer"})

# Email regex: minimal validation per design.
_EMAIL_PATTERN = re.compile(r"[^@\s]+@[^@\s]+\.[^@\s]+")

# Field length constraints.
_NAME_MIN = 1
_NAME_MAX = 50
_COMPANY_MAX = 100


def validate_user_create(data: Any) -> dict[str, Any]:
    """Validate and normalize data for user creation.

    Parameters
    ----------
    data:
        Raw input dict from request.get_json().

    Returns
    -------
    Normalized dict with lowercase email, default role and company.

    Raises
    ------
    ValidationError
        If data is not a dict, contains extra or read-only fields, missing
        required fields, invalid types, or violates length/format constraints.
    """
    # Must be a dict (JSON object)
    if not isinstance(data, dict):
        raise ValidationError(
            "Request body must be a JSON object",
            {"given": type(data).__name__},
        )

    # Check for extra fields
    extra = set(data.keys()) - _USER_CREATE_FIELDS
    if extra:
        raise ValidationError(
            "Unknown fields in request body",
            {"fields": sorted(extra)},
        )

    # Check for read-only fields
    read_only = set(data.keys()) & _READ_ONLY_FIELDS
    if read_only:
        raise ValidationError(
            "Read-only fields cannot be provided",
            {"fields": sorted(read_only)},
        )

    # Required fields must be present and be non-empty strings
    for field in ("first_name", "last_name", "email"):
        value = data.get(field)
        if value is None:
            raise ValidationError(
                f"Missing required field: {field}",
                {"field": field},
            )
        if not isinstance(value, str):
            raise ValidationError(
                f"Field '{field}' must be a string",
                {"field": field, "type": type(value).__name__},
            )
        if len(value) == 0:
            raise ValidationError(
                f"Field '{field}' must not be empty",
                {"field": field},
            )

    # Validate first_name and last_name length
    for field in ("first_name", "last_name"):
        value = data[field]
        if len(value) > _NAME_MAX:
            raise ValidationError(
                f"Field '{field}' exceeds maximum length of {_NAME_MAX}",
                {"field": field, "length": len(value), "max": _NAME_MAX},
            )

    # Validate email format and normalize
    email = data["email"]
    if not _EMAIL_PATTERN.fullmatch(email):
        raise ValidationError(
            "Field 'email' is not a valid email address",
            {"field": "email", "value": email},
        )

    # Optional fields: company and role
    if "company" in data:
        company = data["company"]
        if company is not None and not isinstance(company, str):
            raise ValidationError(
                "Field 'company' must be a string or null",
                {"field": "company", "type": type(company).__name__},
            )
        if isinstance(company, str) and len(company) > _COMPANY_MAX:
            raise ValidationError(
                f"Field 'company' exceeds maximum length of {_COMPANY_MAX}",
                {"field": "company", "length": len(company), "max": _COMPANY_MAX},
            )

    if "role" in data:
        role = data["role"]
        if role not in _VALID_ROLES:
            raise ValidationError(
                f"Field 'role' must be one of {_VALID_ROLES}",
                {"field": "role", "value": role},
            )

    # Build normalized output (never modify input)
    result = {
        "first_name": data["first_name"],
        "last_name": data["last_name"],
        "email": email.lower(),  # Normalize email to lowercase
        "company": data.get("company"),
        "role": data.get("role", "attendee"),  # Default role
    }

    return result


def validate_user_update(data: Any) -> dict[str, Any]:
    """Validate and normalize data for user update (PUT/PATCH).

    Parameters
    ----------
    data:
        Raw input dict from request.get_json().

    Returns
    -------
    Normalized dict with lowercase email (if present), validated fields.

    Raises
    ------
    ValidationError
        If data is not a dict, contains extra or read-only fields, or
        violates constraints for present fields.
    """
    # Must be a dict (JSON object)
    if not isinstance(data, dict):
        raise ValidationError(
            "Request body must be a JSON object",
            {"given": type(data).__name__},
        )

    # Check for extra fields
    extra = set(data.keys()) - _USER_UPDATE_FIELDS
    if extra:
        raise ValidationError(
            "Unknown fields in request body",
            {"fields": sorted(extra)},
        )

    # Check for read-only fields
    read_only = set(data.keys()) & _READ_ONLY_FIELDS
    if read_only:
        raise ValidationError(
            "Read-only fields cannot be provided",
            {"fields": sorted(read_only)},
        )

    # If empty object, it's valid
    if not data:
        return {}

    # Validate each present field
    result = {}

    if "first_name" in data:
        value = data["first_name"]
        if not isinstance(value, str):
            raise ValidationError(
                "Field 'first_name' must be a string",
                {"field": "first_name", "type": type(value).__name__},
            )
        if len(value) == 0:
            raise ValidationError(
                "Field 'first_name' must not be empty",
                {"field": "first_name"},
            )
        if len(value) > _NAME_MAX:
            raise ValidationError(
                f"Field 'first_name' exceeds maximum length of {_NAME_MAX}",
                {"field": "first_name", "length": len(value), "max": _NAME_MAX},
            )
        result["first_name"] = value

    if "last_name" in data:
        value = data["last_name"]
        if not isinstance(value, str):
            raise ValidationError(
                "Field 'last_name' must be a string",
                {"field": "last_name", "type": type(value).__name__},
            )
        if len(value) == 0:
            raise ValidationError(
                "Field 'last_name' must not be empty",
                {"field": "last_name"},
            )
        if len(value) > _NAME_MAX:
            raise ValidationError(
                f"Field 'last_name' exceeds maximum length of {_NAME_MAX}",
                {"field": "last_name", "length": len(value), "max": _NAME_MAX},
            )
        result["last_name"] = value

    if "email" in data:
        email = data["email"]
        if not isinstance(email, str):
            raise ValidationError(
                "Field 'email' must be a string",
                {"field": "email", "type": type(email).__name__},
            )
        if len(email) == 0:
            raise ValidationError(
                "Field 'email' must not be empty",
                {"field": "email"},
            )
        if not _EMAIL_PATTERN.fullmatch(email):
            raise ValidationError(
                "Field 'email' is not a valid email address",
                {"field": "email", "value": email},
            )
        result["email"] = email.lower()  # Normalize

    if "company" in data:
        company = data["company"]
        if company is not None and not isinstance(company, str):
            raise ValidationError(
                "Field 'company' must be a string or null",
                {"field": "company", "type": type(company).__name__},
            )
        if isinstance(company, str) and len(company) > _COMPANY_MAX:
            raise ValidationError(
                f"Field 'company' exceeds maximum length of {_COMPANY_MAX}",
                {"field": "company", "length": len(company), "max": _COMPANY_MAX},
            )
        result["company"] = company

    if "role" in data:
        role = data["role"]
        if role not in _VALID_ROLES:
            raise ValidationError(
                f"Field 'role' must be one of {_VALID_ROLES}",
                {"field": "role", "value": role},
            )
        result["role"] = role

    return result


def validate_pagination(
    page: str | None, page_size: str | None
) -> tuple[int, int]:
    """Validate and normalize pagination query parameters.

    Parameters
    ----------
    page:
        Page number from query string.
    page_size:
        Page size from query string.

    Returns
    -------
    (page, page_size) as positive integers with defaults applied.

    Raises
    ------
    ValidationError
        If page or page_size cannot be parsed as positive integers, or
        page_size exceeds the maximum of 100.
    """
    # Default values
    p = 1
    ps = 20

    # Parse page
    if page is not None:
        try:
            p = int(page)
        except (ValueError, TypeError):
            raise ValidationError(
                "Query parameter 'page' must be an integer",
                {"parameter": "page", "value": page},
            )
        if p < 1:
            raise ValidationError(
                "Query parameter 'page' must be at least 1",
                {"parameter": "page", "value": page},
            )

    # Parse page_size
    if page_size is not None:
        try:
            ps = int(page_size)
        except (ValueError, TypeError):
            raise ValidationError(
                "Query parameter 'page_size' must be an integer",
                {"parameter": "page_size", "value": page_size},
            )
        if ps < 1:
            raise ValidationError(
                "Query parameter 'page_size' must be at least 1",
                {"parameter": "page_size", "value": page_size},
            )
        if ps > 100:
            raise ValidationError(
                "Query parameter 'page_size' cannot exceed 100",
                {"parameter": "page_size", "value": page_size, "max": 100},
            )

    return p, ps


def validate_role_filter(role: str | None) -> str | None:
    """Validate and normalize role filter.

    Parameters
    ----------
    role:
        Role value from query string.

    Returns
    -------
    Normalized role (lowercase) or None if not provided.

    Raises
    ------
    ValidationError
        If role is provided but not in the valid set.
    """
    if role is None:
        return None

    if role not in _VALID_ROLES:
        raise ValidationError(
            f"Query parameter 'role' must be one of {_VALID_ROLES}",
            {"parameter": "role", "value": role},
        )

    return role.lower()

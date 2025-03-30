"""
Exceptions for the ClickUp API client.

This module defines custom exceptions for better error handling.
"""

from typing import Any, Dict, Optional


class ClickUpError(Exception):
    """Base exception for all ClickUp-related errors."""

    def __init__(
        self,
        message: str,
        status_code: Optional[int] = None,
        response: Optional[Dict[str, Any]] = None,
    ):
        self.status_code = status_code
        self.response = response
        self.message = message
        super().__init__(message)

    def __str__(self) -> str:
        """String representation of the error with status code if available."""
        if self.status_code:
            return f"({self.status_code}) {self.message}"
        return self.message


class AuthenticationError(ClickUpError):
    """Raised when authentication with the ClickUp API fails."""

    pass


class RateLimitExceeded(ClickUpError):
    """Raised when the ClickUp API rate limit is exceeded."""

    pass


class ResourceNotFound(ClickUpError):
    """Raised when a requested resource is not found."""

    pass


class ValidationError(ClickUpError):
    """Raised when the API rejects the request due to validation errors."""

    pass

"""Base exception classes for the Madcrow application."""

from typing import Any
from uuid import uuid4


class MadcrowError(Exception):
    """
    Base exception class for all Madcrow application errors.

    Provides consistent error handling with error codes, context,
    and structured logging support.
    """

    def __init__(
        self,
        message: str,
        error_code: str | None = None,
        context: dict[str, Any] | None = None,
        cause: Exception | None = None,
    ) -> None:
        """
        Initialize a Madcrow error.

        Args:
            message: Human-readable error message
            error_code: Unique error code for categorization
            context: Additional context information
            cause: Original exception that caused this error
        """
        super().__init__(message)
        self.message = message
        self.error_code = error_code or self._generate_error_code()
        self.context = context or {}
        self.cause = cause
        self.error_id = str(uuid4())

    def _generate_error_code(self) -> str:
        """Generate a default error code based on the exception class name."""
        class_name = self.__class__.__name__
        # Convert CamelCase to UPPER_SNAKE_CASE
        import re

        return re.sub(r"(?<!^)(?=[A-Z])", "_", class_name).upper()

    def to_dict(self) -> dict[str, Any]:
        """Convert the exception to a dictionary for serialization."""
        return {
            "error_id": self.error_id,
            "error_code": self.error_code,
            "message": self.message,
            "context": self.context,
            "type": self.__class__.__name__,
        }

    def __str__(self) -> str:
        """String representation of the error."""
        context_str = f" (Context: {self.context})" if self.context else ""
        return f"[{self.error_code}] {self.message}{context_str}"


class MadcrowHTTPError(MadcrowError):
    """
    Base HTTP exception class that maps to specific HTTP status codes.

    This exception is designed to be caught by FastAPI exception handlers
    and converted to appropriate HTTP responses.
    """

    def __init__(
        self,
        message: str,
        status_code: int,
        error_code: str | None = None,
        context: dict[str, Any] | None = None,
        cause: Exception | None = None,
        headers: dict[str, str] | None = None,
    ) -> None:
        """
        Initialize an HTTP error.

        Args:
            message: Human-readable error message
            status_code: HTTP status code
            error_code: Unique error code for categorization
            context: Additional context information
            cause: Original exception that caused this error
            headers: Additional HTTP headers to include in response
        """
        super().__init__(message, error_code, context, cause)
        self.status_code = status_code
        self.headers = headers or {}

    def to_http_response_dict(self) -> dict[str, Any]:
        """Convert to dictionary suitable for HTTP response."""
        response_data: dict[str, Any] = {
            "error": True,
            "code": self.error_code,
            "message": self.message,
            "error_id": self.error_id,
        }

        # Include context in development/debug mode only
        # This should be controlled by configuration
        if self.context:
            response_data["context"] = self.context

        return response_data

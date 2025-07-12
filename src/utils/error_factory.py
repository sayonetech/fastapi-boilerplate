"""Error factory utilities for creating standardized errors."""

import hashlib
import logging
from typing import Any
from uuid import UUID

from fastapi import HTTPException, Request
from pydantic import ValidationError as PydanticValidationError

from ..exceptions import (
    AccountAlreadyExistsError,
    AccountNotFoundError,
    AuthenticationError,
    AuthorizationError,
    DatabaseError,
    DuplicateRecordError,
    InvalidInputError,
    MadcrowHTTPError,
    RecordNotFoundError,
    SchemaValidationError,
    ValidationError,
)
from ..models.errors import (
    BaseErrorResponse,
    ErrorDetail,
    InternalServerErrorResponse,
    ValidationErrorResponse,
)

logger = logging.getLogger(__name__)


def _generate_deterministic_id(input_string: str, prefix: str = "", length: int = 8) -> str:
    """
    Generate a deterministic ID from an input string using MD5 hash.

    Args:
        input_string: The input string to hash
        prefix: Optional prefix for the ID
        length: Length of the hash portion (default: 8)

    Returns:
        Deterministic ID string
    """
    # Use MD5 for deterministic hashing (not for security, just for consistent IDs)
    hash_object = hashlib.md5(input_string.encode("utf-8"), usedforsecurity=False)  # nosec B324
    hash_hex = hash_object.hexdigest()[:length]

    if prefix:
        return f"{prefix}-{hash_hex}"
    return hash_hex


class ErrorFactory:
    """Factory class for creating standardized errors and error responses."""

    @staticmethod
    def create_validation_error(
        field: str,
        message: str,
        value: Any | None = None,
        error_code: str = "VALIDATION_ERROR",
    ) -> ValidationError:
        """Create a validation error for a specific field."""
        return InvalidInputError(
            field=field,
            value=value,
            message=message,
            context={"error_code": error_code},
        )

    @staticmethod
    def create_account_not_found_error(
        account_id: UUID | None = None,
        email: str | None = None,
    ) -> AccountNotFoundError:
        """Create an account not found error."""
        return AccountNotFoundError(account_id=account_id, email=email)

    @staticmethod
    def create_account_exists_error(email: str) -> AccountAlreadyExistsError:
        """Create an account already exists error."""
        return AccountAlreadyExistsError(email=email)

    @staticmethod
    def create_authentication_error(
        message: str = "Authentication failed",
        context: dict[str, Any] | None = None,
    ) -> AuthenticationError:
        """Create an authentication error."""
        return AuthenticationError(message=message, context=context)

    @staticmethod
    def create_authorization_error(
        message: str = "Access denied",
        required_permission: str | None = None,
        resource: str | None = None,
    ) -> AuthorizationError:
        """Create an authorization error."""
        context = {}
        if resource:
            context["resource"] = resource
        return AuthorizationError(
            message=message,
            required_permission=required_permission,
            context=context if context else None,
        )

    @staticmethod
    def create_database_error(
        message: str,
        operation: str | None = None,
        table: str | None = None,
        cause: Exception | None = None,
    ) -> DatabaseError:
        """Create a database error."""
        return DatabaseError(
            message=message,
            operation=operation,
            table=table,
            cause=cause,
        )

    @staticmethod
    def create_record_not_found_error(
        table: str,
        identifier: str | None = None,
    ) -> RecordNotFoundError:
        """Create a record not found error."""
        return RecordNotFoundError(table=table, identifier=identifier)

    @staticmethod
    def create_duplicate_record_error(
        table: str,
        field: str | None = None,
        value: str | None = None,
    ) -> DuplicateRecordError:
        """Create a duplicate record error."""
        return DuplicateRecordError(table=table, field=field, value=value)


class ErrorResponseFactory:
    """Factory class for creating standardized error responses."""

    @staticmethod
    def from_exception(
        exception: Exception,
        request: Request | None = None,
        include_debug_info: bool = False,
    ) -> dict[str, Any]:
        """
        Create an error response from an exception.

        Args:
            exception: The exception to convert
            request: Optional request object for context
            include_debug_info: Whether to include debug information

        Returns:
            Dictionary suitable for JSON response
        """
        if isinstance(exception, MadcrowHTTPError):
            return ErrorResponseFactory._from_madcrow_http_error(exception, request, include_debug_info)
        elif isinstance(exception, PydanticValidationError):
            return ErrorResponseFactory._from_pydantic_validation_error(exception, request)
        elif isinstance(exception, HTTPException):
            return ErrorResponseFactory._from_http_exception(exception, request)
        else:
            return ErrorResponseFactory._from_generic_exception(exception, request, include_debug_info)

    @staticmethod
    def _from_madcrow_http_error(
        exception: MadcrowHTTPError,
        request: Request | None = None,
        include_debug_info: bool = False,
    ) -> dict[str, Any]:
        """Create response from MadcrowHTTPError."""
        response_data = exception.to_http_response_dict()

        # Add request context if available
        if request:
            response_data["path"] = str(request.url.path)
            response_data["method"] = request.method

        # Add debug info if requested
        if include_debug_info and exception.cause:
            response_data["debug"] = {
                "cause": str(exception.cause),
                "cause_type": type(exception.cause).__name__,
            }

        return response_data

    @staticmethod
    def _from_pydantic_validation_error(
        exception: PydanticValidationError,
        request: Request | None = None,
    ) -> dict[str, Any]:
        """Create response from Pydantic validation error."""
        error_details = []
        for error in exception.errors():
            field_path = ".".join(str(loc) for loc in error["loc"])
            error_details.append(
                ErrorDetail(
                    field=field_path,
                    message=error["msg"],
                    code=error["type"].upper(),
                    value=error.get("input"),
                )
            )

        schema_error = SchemaValidationError(errors=[{"field": d.field, "message": d.message} for d in error_details])

        response = ValidationErrorResponse(
            error=True,
            code=schema_error.error_code,
            message=schema_error.message,
            error_id=schema_error.error_id,
            details=error_details,
        )

        return response.model_dump()

    @staticmethod
    def _from_http_exception(
        exception: HTTPException,
        request: Request | None = None,
    ) -> dict[str, Any]:
        """Create response from FastAPI HTTPException."""
        response = BaseErrorResponse(
            error=True,
            code="HTTP_EXCEPTION",
            message=str(exception.detail),
            error_id=_generate_deterministic_id(str(exception.detail), "http"),
        )

        response_data = response.model_dump()
        if request:
            response_data["path"] = str(request.url.path)
            response_data["method"] = request.method

        return response_data

    @staticmethod
    def _from_generic_exception(
        exception: Exception,
        request: Request | None = None,
        include_debug_info: bool = False,
    ) -> dict[str, Any]:
        """Create response from generic exception."""
        # Log the unexpected exception
        logger.exception("Unexpected exception occurred", exc_info=exception)

        # Generate deterministic IDs based on exception details
        exception_string = f"{type(exception).__name__}:{str(exception)}"
        error_id = _generate_deterministic_id(exception_string, "internal")
        support_ref = _generate_deterministic_id(exception_string, "ERR", 10)

        response = InternalServerErrorResponse(
            error=True,
            code="INTERNAL_SERVER_ERROR",
            message="An unexpected error occurred",
            error_id=error_id,
            support_reference=support_ref,
        )

        response_data = response.model_dump()

        if include_debug_info:
            response_data["debug"] = {
                "exception_type": type(exception).__name__,
                "exception_message": str(exception),
            }

        if request:
            response_data["path"] = str(request.url.path)
            response_data["method"] = request.method

        return response_data

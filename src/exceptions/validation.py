"""Validation-related exception classes."""

from typing import Any

from .base import MadcrowHTTPError


class ValidationError(MadcrowHTTPError):
    """Base exception for validation errors."""

    def __init__(
        self,
        message: str,
        field: str | None = None,
        value: Any | None = None,
        context: dict[str, Any] | None = None,
    ) -> None:
        validation_context = context or {}
        if field:
            validation_context["field"] = field
        if value is not None:
            validation_context["value"] = str(value)

        super().__init__(
            message=message,
            status_code=422,
            error_code="VALIDATION_ERROR",
            context=validation_context,
        )


class InvalidInputError(ValidationError):
    """Raised when input data is invalid."""

    def __init__(
        self,
        field: str,
        value: Any | None = None,
        expected: str | None = None,
        context: dict[str, Any] | None = None,
        message: str | None = None,
    ) -> None:
        validation_context = context or {}
        if expected:
            validation_context["expected"] = expected

        # Use custom message if provided, otherwise generate default message
        if message:
            error_message = message
        else:
            error_message = f"Invalid value for field '{field}'"
            if expected:
                error_message += f", expected {expected}"
            if value is not None:
                error_message += f", got: {value}"

        super().__init__(
            message=error_message,
            field=field,
            value=value,
            context=validation_context,
        )


class MissingFieldError(ValidationError):
    """Raised when a required field is missing."""

    def __init__(
        self,
        field: str,
        context: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(
            message=f"Required field '{field}' is missing",
            field=field,
            context=context,
        )


class InvalidFieldValueError(ValidationError):
    """Raised when a field has an invalid value."""

    def __init__(
        self,
        field: str,
        value: Any,
        allowed_values: list[Any] | None = None,
        pattern: str | None = None,
        context: dict[str, Any] | None = None,
    ) -> None:
        validation_context = context or {}

        message = f"Invalid value '{value}' for field '{field}'"

        if allowed_values:
            validation_context["allowed_values"] = allowed_values
            message += f", allowed values: {allowed_values}"
        elif pattern:
            validation_context["pattern"] = pattern
            message += f", must match pattern: {pattern}"

        super().__init__(
            message=message,
            field=field,
            value=value,
            context=validation_context,
        )


class SchemaValidationError(ValidationError):
    """Raised when schema validation fails."""

    def __init__(
        self,
        errors: list[dict[str, Any]],
        schema_name: str | None = None,
        context: dict[str, Any] | None = None,
    ) -> None:
        validation_context = context or {}
        validation_context["validation_errors"] = errors
        if schema_name:
            validation_context["schema"] = schema_name

        # Create a summary message
        error_count = len(errors)
        message = f"Schema validation failed with {error_count} error"
        if error_count != 1:
            message += "s"
        if schema_name:
            message += f" for {schema_name}"

        super().__init__(
            message=message,
            context=validation_context,
        )


class EmailValidationError(ValidationError):
    """Raised when email validation fails."""

    def __init__(
        self,
        email: str,
        reason: str | None = None,
        context: dict[str, Any] | None = None,
    ) -> None:
        validation_context = context or {}
        if reason:
            validation_context["reason"] = reason

        message = f"Invalid email address: {email}"
        if reason:
            message += f" ({reason})"

        super().__init__(
            message=message,
            field="email",
            value=email,
            context=validation_context,
        )


class PasswordValidationError(ValidationError):
    """Raised when password validation fails."""

    def __init__(
        self,
        requirements: list[str],
        context: dict[str, Any] | None = None,
    ) -> None:
        validation_context = context or {}
        validation_context["failed_requirements"] = requirements

        message = "Password does not meet requirements: " + ", ".join(requirements)

        super().__init__(
            message=message,
            field="password",
            context=validation_context,
        )


class DateValidationError(ValidationError):
    """Raised when date validation fails."""

    def __init__(
        self,
        field: str,
        value: str,
        expected_format: str | None = None,
        context: dict[str, Any] | None = None,
    ) -> None:
        validation_context = context or {}
        if expected_format:
            validation_context["expected_format"] = expected_format

        message = f"Invalid date format for field '{field}': {value}"
        if expected_format:
            message += f", expected format: {expected_format}"

        super().__init__(
            message=message,
            field=field,
            value=value,
            context=validation_context,
        )

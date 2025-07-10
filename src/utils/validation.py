"""Validation utilities and custom validators."""

import re
from typing import Any
from uuid import UUID

from pydantic import validator

from ..exceptions import (
    EmailValidationError,
    InvalidFieldValueError,
    PasswordValidationError,
)


class ValidationUtils:
    """Utility class for common validation operations."""

    # Email validation regex (basic but effective)
    EMAIL_REGEX = re.compile(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")

    # Password requirements
    PASSWORD_MIN_LENGTH = 8
    PASSWORD_MAX_LENGTH = 128

    @classmethod
    def validate_email(cls, email: str) -> str:
        """
        Validate email format.

        Args:
            email: Email address to validate

        Returns:
            Validated email address

        Raises:
            EmailValidationError: If email format is invalid
        """
        if not email:
            raise EmailValidationError(email, "Email cannot be empty")

        if not cls.EMAIL_REGEX.match(email):
            raise EmailValidationError(email, "Invalid email format")

        if len(email) > 254:  # RFC 5321 limit
            raise EmailValidationError(email, "Email address too long")

        return email.lower().strip()

    @classmethod
    def validate_password(cls, password: str) -> str:
        """
        Validate password strength.

        Args:
            password: Password to validate

        Returns:
            Validated password

        Raises:
            PasswordValidationError: If password doesn't meet requirements
        """
        if not password:
            raise PasswordValidationError(["Password cannot be empty"])

        failed_requirements = []

        if len(password) < cls.PASSWORD_MIN_LENGTH:
            failed_requirements.append(f"Must be at least {cls.PASSWORD_MIN_LENGTH} characters long")

        if len(password) > cls.PASSWORD_MAX_LENGTH:
            failed_requirements.append(f"Must be no more than {cls.PASSWORD_MAX_LENGTH} characters long")

        if not re.search(r"[A-Z]", password):
            failed_requirements.append("Must contain at least one uppercase letter")

        if not re.search(r"[a-z]", password):
            failed_requirements.append("Must contain at least one lowercase letter")

        if not re.search(r"\d", password):
            failed_requirements.append("Must contain at least one digit")

        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            failed_requirements.append("Must contain at least one special character")

        if failed_requirements:
            raise PasswordValidationError(failed_requirements)

        return password

    @classmethod
    def validate_uuid(cls, value: Any, field_name: str = "id") -> UUID:
        """
        Validate UUID format.

        Args:
            value: Value to validate as UUID
            field_name: Name of the field being validated

        Returns:
            Validated UUID

        Raises:
            InvalidFieldValueError: If value is not a valid UUID
        """
        if isinstance(value, UUID):
            return value

        if isinstance(value, str):
            try:
                return UUID(value)
            except ValueError:
                raise InvalidFieldValueError(
                    field=field_name,
                    value=value,
                    pattern="Valid UUID format (e.g., 123e4567-e89b-12d3-a456-426614174000)",
                )

        raise InvalidFieldValueError(field=field_name, value=value, pattern="Valid UUID string or UUID object")

    @classmethod
    def validate_string_length(
        cls,
        value: str,
        field_name: str,
        min_length: int | None = None,
        max_length: int | None = None,
    ) -> str:
        """
        Validate string length constraints.

        Args:
            value: String value to validate
            field_name: Name of the field being validated
            min_length: Minimum allowed length
            max_length: Maximum allowed length

        Returns:
            Validated string

        Raises:
            InvalidFieldValueError: If string length is invalid
        """
        if not isinstance(value, str):
            raise InvalidFieldValueError(field=field_name, value=value, pattern="String value")

        length = len(value)

        if min_length is not None and length < min_length:
            raise InvalidFieldValueError(field=field_name, value=value, pattern=f"At least {min_length} characters")

        if max_length is not None and length > max_length:
            raise InvalidFieldValueError(field=field_name, value=value, pattern=f"At most {max_length} characters")

        return value.strip()

    @classmethod
    def validate_choice(
        cls,
        value: Any,
        field_name: str,
        allowed_values: list[Any],
    ) -> Any:
        """
        Validate that value is in allowed choices.

        Args:
            value: Value to validate
            field_name: Name of the field being validated
            allowed_values: List of allowed values

        Returns:
            Validated value

        Raises:
            InvalidFieldValueError: If value is not in allowed choices
        """
        if value not in allowed_values:
            raise InvalidFieldValueError(field=field_name, value=value, allowed_values=allowed_values)

        return value


def create_pydantic_validators():
    """
    Create Pydantic validators using the validation utilities.

    Returns:
        Dictionary of validator functions that can be used in Pydantic models
    """

    @validator("email", pre=True)
    def validate_email_field(cls, v):
        """Pydantic validator for email fields."""
        if v is None:
            return v
        return ValidationUtils.validate_email(v)

    @validator("password", pre=True)
    def validate_password_field(cls, v):
        """Pydantic validator for password fields."""
        if v is None:
            return v
        return ValidationUtils.validate_password(v)

    def validate_uuid_field(field_name: str = "id"):
        """Create a UUID validator for a specific field."""

        @validator(field_name, pre=True)
        def _validate_uuid(cls, v):
            if v is None:
                return v
            return ValidationUtils.validate_uuid(v, field_name)

        return _validate_uuid

    def validate_string_length_field(
        field_name: str,
        min_length: int | None = None,
        max_length: int | None = None,
    ):
        """Create a string length validator for a specific field."""

        @validator(field_name, pre=True)
        def _validate_string_length(cls, v):
            if v is None:
                return v
            return ValidationUtils.validate_string_length(v, field_name, min_length, max_length)

        return _validate_string_length

    def validate_choice_field(field_name: str, allowed_values: list[Any]):
        """Create a choice validator for a specific field."""

        @validator(field_name, pre=True)
        def _validate_choice(cls, v):
            if v is None:
                return v
            return ValidationUtils.validate_choice(v, field_name, allowed_values)

        return _validate_choice

    return {
        "email": validate_email_field,
        "password": validate_password_field,
        "uuid": validate_uuid_field,
        "string_length": validate_string_length_field,
        "choice": validate_choice_field,
    }

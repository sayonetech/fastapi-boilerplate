"""Custom exception classes for the Madcrow application."""

from .base import (
    MadcrowError,
    MadcrowHTTPError,
)
from .business import (
    AccountAlreadyExistsError,
    AccountBannedError,
    AccountClosedError,
    AccountError,
    AccountLoginError,
    AccountNotFoundError,
    AccountNotVerifiedError,
    AuthenticationError,
    AuthorizationError,
    InvalidAccountStatusError,
    PermissionDeniedError,
    RateLimitExceededError,
)
from .database import (
    DatabaseConnectionError,
    DatabaseError,
    DatabaseTransactionError,
    DuplicateRecordError,
    RecordNotFoundError,
)
from .validation import (
    DateValidationError,
    EmailValidationError,
    InvalidFieldValueError,
    InvalidInputError,
    MissingFieldError,
    PasswordValidationError,
    SchemaValidationError,
    ValidationError,
)

__all__ = [
    "AccountAlreadyExistsError",
    "AccountBannedError",
    "AccountClosedError",
    "AccountError",
    "AccountLoginError",
    "AccountNotFoundError",
    "AccountNotVerifiedError",
    "AuthenticationError",
    "AuthorizationError",
    "DatabaseConnectionError",
    "DatabaseError",
    "DatabaseTransactionError",
    "DateValidationError",
    "DuplicateRecordError",
    "EmailValidationError",
    "InvalidAccountStatusError",
    "InvalidFieldValueError",
    "InvalidInputError",
    "MadcrowError",
    "MadcrowHTTPError",
    "MissingFieldError",
    "PasswordValidationError",
    "PermissionDeniedError",
    "RateLimitExceededError",
    "RecordNotFoundError",
    "SchemaValidationError",
    "ValidationError",
]

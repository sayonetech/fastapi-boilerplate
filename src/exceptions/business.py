"""Business logic exception classes."""

from typing import Any
from uuid import UUID

from .base import MadcrowHTTPError


class AccountError(MadcrowHTTPError):
    """Base exception for account-related errors."""

    def __init__(
        self,
        message: str,
        status_code: int = 400,
        error_code: str | None = None,
        context: dict[str, Any] | None = None,
        cause: Exception | None = None,
    ) -> None:
        super().__init__(message, status_code, error_code, context, cause)


class AccountNotFoundError(AccountError):
    """Raised when an account cannot be found."""

    def __init__(
        self,
        account_id: UUID | None = None,
        email: str | None = None,
        context: dict[str, Any] | None = None,
    ) -> None:
        # Build context with search criteria
        search_context = context or {}
        if account_id:
            search_context["account_id"] = str(account_id)
        if email:
            search_context["email"] = email

        # Create appropriate message
        if account_id:
            message = f"Account with ID {account_id} not found"
        elif email:
            message = f"Account with email {email} not found"
        else:
            message = "Account not found"

        super().__init__(
            message=message,
            status_code=404,
            error_code="ACCOUNT_NOT_FOUND",
            context=search_context,
        )


class AccountAlreadyExistsError(AccountError):
    """Raised when attempting to create an account that already exists."""

    def __init__(
        self,
        email: str,
        context: dict[str, Any] | None = None,
    ) -> None:
        search_context = context or {}
        search_context["email"] = email

        super().__init__(
            message=f"Account with email {email} already exists",
            status_code=409,
            error_code="ACCOUNT_ALREADY_EXISTS",
            context=search_context,
        )


class InvalidAccountStatusError(AccountError):
    """Raised when an account status transition is invalid."""

    def __init__(
        self,
        current_status: str,
        requested_status: str,
        account_id: UUID | None = None,
        context: dict[str, Any] | None = None,
    ) -> None:
        search_context = context or {}
        search_context.update(
            {
                "current_status": current_status,
                "requested_status": requested_status,
            }
        )
        if account_id:
            search_context["account_id"] = str(account_id)

        super().__init__(
            message=f"Cannot change account status from {current_status} to {requested_status}",
            status_code=400,
            error_code="INVALID_ACCOUNT_STATUS_TRANSITION",
            context=search_context,
        )


class AccountNotVerifiedError(AccountError):
    """Raised when attempting to login with an unverified account."""

    def __init__(
        self,
        email: str | None = None,
        account_id: UUID | None = None,
        context: dict[str, Any] | None = None,
    ) -> None:
        search_context = context or {}
        if email:
            search_context["email"] = email
        if account_id:
            search_context["account_id"] = str(account_id)

        super().__init__(
            message="Account is not verified. Please check your email and verify your account.",
            status_code=401,
            error_code="ACCOUNT_NOT_VERIFIED",
            context=search_context,
        )


class AccountBannedError(AccountError):
    """Raised when attempting to login with a banned account."""

    def __init__(
        self,
        message: str = "Account is banned.",
        email: str | None = None,
        account_id: UUID | None = None,
        context: dict[str, Any] | None = None,
    ) -> None:
        search_context = context or {}
        if email:
            search_context["email"] = email
        if account_id:
            search_context["account_id"] = str(account_id)

        super().__init__(
            message=message,
            status_code=401,
            error_code="ACCOUNT_BANNED",
            context=search_context,
        )


class AccountClosedError(AccountError):
    """Raised when attempting to login with a closed account."""

    def __init__(
        self,
        message: str = "Account is closed.",
        email: str | None = None,
        account_id: UUID | None = None,
        context: dict[str, Any] | None = None,
    ) -> None:
        search_context = context or {}
        if email:
            search_context["email"] = email
        if account_id:
            search_context["account_id"] = str(account_id)

        super().__init__(
            message=message,
            status_code=401,
            error_code="ACCOUNT_CLOSED",
            context=search_context,
        )


class AccountLoginError(AccountError):
    """Raised when account cannot login for various reasons."""

    def __init__(
        self,
        message: str,
        email: str | None = None,
        account_id: UUID | None = None,
        context: dict[str, Any] | None = None,
    ) -> None:
        search_context = context or {}
        if email:
            search_context["email"] = email
        if account_id:
            search_context["account_id"] = str(account_id)

        super().__init__(
            message=message,
            status_code=401,
            error_code="ACCOUNT_LOGIN_ERROR",
            context=search_context,
        )


class AuthenticationError(MadcrowHTTPError):
    """Raised when authentication fails."""

    def __init__(
        self,
        message: str = "Authentication failed",
        context: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(
            message=message,
            status_code=401,
            error_code="AUTHENTICATION_FAILED",
            context=context,
            headers={"WWW-Authenticate": "Bearer"},
        )


class AuthorizationError(MadcrowHTTPError):
    """Raised when authorization fails."""

    def __init__(
        self,
        message: str = "Access denied",
        required_permission: str | None = None,
        context: dict[str, Any] | None = None,
    ) -> None:
        auth_context = context or {}
        if required_permission:
            auth_context["required_permission"] = required_permission

        super().__init__(
            message=message,
            status_code=403,
            error_code="AUTHORIZATION_FAILED",
            context=auth_context,
        )


class PermissionDeniedError(AuthorizationError):
    """Raised when a specific permission is denied."""

    def __init__(
        self,
        permission: str,
        resource: str | None = None,
        context: dict[str, Any] | None = None,
    ) -> None:
        perm_context = context or {}
        perm_context["permission"] = permission
        if resource:
            perm_context["resource"] = resource

        message = f"Permission denied: {permission}"
        if resource:
            message += f" on {resource}"

        super().__init__(
            message=message,
            required_permission=permission,
            context=perm_context,
        )


class RateLimitExceededError(MadcrowHTTPError):
    """Raised when rate limit is exceeded."""

    def __init__(
        self,
        identifier: str,
        max_attempts: int,
        time_window: int,
        retry_after: int,
        context: dict[str, Any] | None = None,
    ) -> None:
        # Build context with rate limit details
        rate_limit_context = context or {}
        rate_limit_context.update(
            {
                "identifier": identifier,
                "max_attempts": max_attempts,
                "time_window": time_window,
                "retry_after": retry_after,
            }
        )

        message = f"Rate limit exceeded for {identifier}. Try again in {retry_after} seconds."

        super().__init__(
            message=message,
            status_code=429,
            error_code="RATE_LIMIT_EXCEEDED",
            context=rate_limit_context,
        )

"""Database-related exception classes."""

from typing import Any

from .base import MadcrowError, MadcrowHTTPError


class DatabaseError(MadcrowError):
    """Base exception for database-related errors."""

    def __init__(
        self,
        message: str,
        error_code: str | None = None,
        context: dict[str, Any] | None = None,
        cause: Exception | None = None,
        operation: str | None = None,
        table: str | None = None,
    ) -> None:
        db_context = context or {}
        if operation:
            db_context["operation"] = operation
        if table:
            db_context["table"] = table

        super().__init__(message, error_code, db_context, cause)
        self.operation = operation
        self.table = table


class DatabaseConnectionError(DatabaseError):
    """Raised when database connection fails."""

    def __init__(
        self,
        message: str = "Database connection failed",
        context: dict[str, Any] | None = None,
        cause: Exception | None = None,
    ) -> None:
        super().__init__(
            message=message,
            error_code="DATABASE_CONNECTION_FAILED",
            context=context,
            cause=cause,
        )


class DatabaseTransactionError(DatabaseError):
    """Raised when a database transaction fails."""

    def __init__(
        self,
        message: str = "Database transaction failed",
        operation: str | None = None,
        context: dict[str, Any] | None = None,
        cause: Exception | None = None,
    ) -> None:
        super().__init__(
            message=message,
            error_code="DATABASE_TRANSACTION_FAILED",
            context=context,
            cause=cause,
            operation=operation,
        )


class RecordNotFoundError(MadcrowHTTPError):
    """Raised when a database record is not found."""

    def __init__(
        self,
        table: str,
        identifier: str | None = None,
        context: dict[str, Any] | None = None,
    ) -> None:
        record_context = context or {}
        record_context["table"] = table
        if identifier:
            record_context["identifier"] = identifier

        message = f"Record not found in {table}"
        if identifier:
            message += f" with identifier {identifier}"

        super().__init__(
            message=message,
            status_code=404,
            error_code="RECORD_NOT_FOUND",
            context=record_context,
        )


class DuplicateRecordError(MadcrowHTTPError):
    """Raised when attempting to create a duplicate record."""

    def __init__(
        self,
        table: str,
        field: str | None = None,
        value: str | None = None,
        context: dict[str, Any] | None = None,
    ) -> None:
        dup_context = context or {}
        dup_context["table"] = table
        if field:
            dup_context["field"] = field
        if value:
            dup_context["value"] = value

        message = f"Duplicate record in {table}"
        if field and value:
            message += f": {field} = {value}"
        elif field:
            message += f" for field {field}"

        super().__init__(
            message=message,
            status_code=409,
            error_code="DUPLICATE_RECORD",
            context=dup_context,
        )


class DatabaseIntegrityError(DatabaseError):
    """Raised when database integrity constraints are violated."""

    def __init__(
        self,
        message: str,
        constraint: str | None = None,
        table: str | None = None,
        context: dict[str, Any] | None = None,
        cause: Exception | None = None,
    ) -> None:
        integrity_context = context or {}
        if constraint:
            integrity_context["constraint"] = constraint

        super().__init__(
            message=message,
            error_code="DATABASE_INTEGRITY_ERROR",
            context=integrity_context,
            cause=cause,
            table=table,
        )


class DatabaseTimeoutError(DatabaseError):
    """Raised when database operations timeout."""

    def __init__(
        self,
        operation: str,
        timeout_seconds: float | None = None,
        context: dict[str, Any] | None = None,
        cause: Exception | None = None,
    ) -> None:
        timeout_context = context or {}
        if timeout_seconds:
            timeout_context["timeout_seconds"] = timeout_seconds

        message = f"Database operation '{operation}' timed out"
        if timeout_seconds:
            message += f" after {timeout_seconds} seconds"

        super().__init__(
            message=message,
            error_code="DATABASE_TIMEOUT",
            context=timeout_context,
            cause=cause,
            operation=operation,
        )

"""Error response models for standardized API error responses."""

from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class ErrorDetail(BaseModel):
    """Individual error detail for validation errors."""

    field: str = Field(..., description="Field name that caused the error")
    message: str = Field(..., description="Error message for this field")
    code: str = Field(..., description="Error code for this specific validation")
    value: Any | None = Field(None, description="The invalid value that was provided")


class ErrorContext(BaseModel):
    """Additional context information for errors."""

    request_id: str | None = Field(None, description="Request ID for tracing")
    timestamp: str | None = Field(None, description="Error timestamp")
    path: str | None = Field(None, description="API path where error occurred")
    method: str | None = Field(None, description="HTTP method")
    user_id: UUID | None = Field(None, description="User ID if authenticated")
    additional_data: dict[str, Any] | None = Field(None, description="Additional error context")


class BaseErrorResponse(BaseModel):
    """Base error response model."""

    error: bool = Field(True, description="Indicates this is an error response")
    code: str = Field(..., description="Error code for categorization")
    message: str = Field(..., description="Human-readable error message")
    error_id: str = Field(..., description="Unique error identifier for tracking")


class ValidationErrorResponse(BaseErrorResponse):
    """Error response for validation failures."""

    details: list[ErrorDetail] = Field(..., description="List of validation errors")


class BusinessErrorResponse(BaseErrorResponse):
    """Error response for business logic errors."""

    context: ErrorContext | None = Field(None, description="Additional error context")


class DatabaseErrorResponse(BaseErrorResponse):
    """Error response for database-related errors."""

    operation: str | None = Field(None, description="Database operation that failed")
    table: str | None = Field(None, description="Database table involved")
    context: ErrorContext | None = Field(None, description="Additional error context")


class AuthenticationErrorResponse(BaseErrorResponse):
    """Error response for authentication failures."""

    auth_scheme: str | None = Field(None, description="Authentication scheme required")


class AuthorizationErrorResponse(BaseErrorResponse):
    """Error response for authorization failures."""

    required_permission: str | None = Field(None, description="Permission required for this operation")
    resource: str | None = Field(None, description="Resource that was being accessed")


class InternalServerErrorResponse(BaseErrorResponse):
    """Error response for internal server errors."""

    support_reference: str | None = Field(None, description="Support reference for tracking")

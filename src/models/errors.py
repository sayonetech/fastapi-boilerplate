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

    class Config:
        """Pydantic configuration."""

        json_schema_extra = {
            "example": {
                "error": True,
                "code": "VALIDATION_ERROR",
                "message": "Invalid input data provided",
                "error_id": "550e8400-e29b-41d4-a716-446655440000",
            }
        }


class ValidationErrorResponse(BaseErrorResponse):
    """Error response for validation failures."""

    details: list[ErrorDetail] = Field(..., description="List of validation errors")

    class Config:
        """Pydantic configuration."""

        json_schema_extra = {
            "example": {
                "error": True,
                "code": "VALIDATION_ERROR",
                "message": "Validation failed for 2 fields",
                "error_id": "550e8400-e29b-41d4-a716-446655440000",
                "details": [
                    {
                        "field": "email",
                        "message": "Invalid email format",
                        "code": "INVALID_EMAIL",
                        "value": "invalid-email",
                    },
                    {
                        "field": "password",
                        "message": "Password must be at least 8 characters",
                        "code": "PASSWORD_TOO_SHORT",
                        "value": None,
                    },
                ],
            }
        }


class BusinessErrorResponse(BaseErrorResponse):
    """Error response for business logic errors."""

    context: ErrorContext | None = Field(None, description="Additional error context")

    class Config:
        """Pydantic configuration."""

        json_schema_extra = {
            "example": {
                "error": True,
                "code": "ACCOUNT_NOT_FOUND",
                "message": "Account with ID 123e4567-e89b-12d3-a456-426614174000 not found",
                "error_id": "550e8400-e29b-41d4-a716-446655440000",
                "context": {
                    "request_id": "req_123456789",
                    "timestamp": "2024-01-15T10:30:00Z",
                    "path": "/v1/accounts/123e4567-e89b-12d3-a456-426614174000",
                    "method": "GET",
                },
            }
        }


class DatabaseErrorResponse(BaseErrorResponse):
    """Error response for database-related errors."""

    operation: str | None = Field(None, description="Database operation that failed")
    table: str | None = Field(None, description="Database table involved")
    context: ErrorContext | None = Field(None, description="Additional error context")

    class Config:
        """Pydantic configuration."""

        json_schema_extra = {
            "example": {
                "error": True,
                "code": "DATABASE_CONNECTION_FAILED",
                "message": "Unable to connect to database",
                "error_id": "550e8400-e29b-41d4-a716-446655440000",
                "operation": "SELECT",
                "table": "accounts",
            }
        }


class AuthenticationErrorResponse(BaseErrorResponse):
    """Error response for authentication failures."""

    auth_scheme: str | None = Field(None, description="Authentication scheme required")

    class Config:
        """Pydantic configuration."""

        json_schema_extra = {
            "example": {
                "error": True,
                "code": "AUTHENTICATION_FAILED",
                "message": "Invalid or expired authentication token",
                "error_id": "550e8400-e29b-41d4-a716-446655440000",
                "auth_scheme": "Bearer",
            }
        }


class AuthorizationErrorResponse(BaseErrorResponse):
    """Error response for authorization failures."""

    required_permission: str | None = Field(None, description="Permission required for this operation")
    resource: str | None = Field(None, description="Resource that was being accessed")

    class Config:
        """Pydantic configuration."""

        json_schema_extra = {
            "example": {
                "error": True,
                "code": "AUTHORIZATION_FAILED",
                "message": "Insufficient permissions to access this resource",
                "error_id": "550e8400-e29b-41d4-a716-446655440000",
                "required_permission": "accounts:read",
                "resource": "account:123e4567-e89b-12d3-a456-426614174000",
            }
        }


class InternalServerErrorResponse(BaseErrorResponse):
    """Error response for internal server errors."""

    support_reference: str | None = Field(None, description="Support reference for tracking")

    class Config:
        """Pydantic configuration."""

        json_schema_extra = {
            "example": {
                "error": True,
                "code": "INTERNAL_SERVER_ERROR",
                "message": "An unexpected error occurred. Please contact support.",
                "error_id": "550e8400-e29b-41d4-a716-446655440000",
                "support_reference": "SUP-2024-001234",
            }
        }

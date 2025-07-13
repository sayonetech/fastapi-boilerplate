"""Event context models for the event system.

This module defines Pydantic models that represent the context/payload
for different types of events in the system.
"""

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class BaseEventContext(BaseModel):
    """Base event context with common fields."""

    timestamp: datetime = Field(default_factory=lambda: datetime.now(), description="Event timestamp")
    request_id: str | None = Field(default=None, description="Request ID for tracing")
    user_agent: str | None = Field(default=None, description="User agent string")
    ip_address: str | None = Field(default=None, description="Client IP address")

    model_config = ConfigDict()


class LoginEventContext(BaseEventContext):
    """Context for user login events."""

    user_id: UUID = Field(..., description="User account ID")
    email: str = Field(..., description="User email address")
    name: str = Field(..., description="User display name")
    is_admin: bool = Field(default=False, description="Whether user is admin")
    remember_me: bool = Field(default=False, description="Whether remember me was selected")
    session_duration: int | None = Field(default=None, description="Session duration in seconds")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "user_id": "123e4567-e89b-12d3-a456-426614174000",
                "email": "user@example.com",
                "name": "John Doe",
                "is_admin": False,
                "remember_me": True,
                "ip_address": "192.168.1.1",
                "user_agent": "Mozilla/5.0...",
                "timestamp": "2024-01-01T12:00:00Z",
            }
        }
    )


class LogoutEventContext(BaseEventContext):
    """Context for user logout events."""

    user_id: UUID = Field(..., description="User account ID")
    email: str = Field(..., description="User email address")
    session_duration: int | None = Field(default=None, description="Session duration in seconds")
    logout_reason: str = Field(default="user_initiated", description="Reason for logout")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "user_id": "123e4567-e89b-12d3-a456-426614174000",
                "email": "user@example.com",
                "logout_reason": "user_initiated",
                "session_duration": 3600,
                "ip_address": "192.168.1.1",
                "timestamp": "2024-01-01T13:00:00Z",
            }
        }
    )


class LoginFailedEventContext(BaseEventContext):
    """Context for failed login attempts."""

    email: str = Field(..., description="Attempted email address")
    failure_reason: str = Field(..., description="Reason for login failure")
    attempt_count: int | None = Field(default=None, description="Number of failed attempts")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "email": "user@example.com",
                "failure_reason": "invalid_credentials",
                "attempt_count": 3,
                "ip_address": "192.168.1.1",
                "user_agent": "Mozilla/5.0...",
                "timestamp": "2024-01-01T12:00:00Z",
            }
        }
    )


class RegistrationEventContext(BaseEventContext):
    """Context for user registration events."""

    user_id: UUID = Field(..., description="New user account ID")
    email: str = Field(..., description="User email address")
    name: str = Field(..., description="User display name")
    account_status: str = Field(..., description="Initial account status")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "user_id": "123e4567-e89b-12d3-a456-426614174000",
                "email": "newuser@example.com",
                "name": "Jane Doe",
                "account_status": "PENDING",
                "ip_address": "192.168.1.1",
                "user_agent": "Mozilla/5.0...",
                "timestamp": "2024-01-01T12:00:00Z",
            }
        }
    )


class GenericEventContext(BaseEventContext):
    """Generic event context for custom events."""

    event_type: str = Field(..., description="Type of the event")
    data: dict[str, Any] = Field(default_factory=dict, description="Event-specific data")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {"event_type": "custom_event", "data": {"key": "value"}, "timestamp": "2024-01-01T12:00:00Z"}
        }
    )

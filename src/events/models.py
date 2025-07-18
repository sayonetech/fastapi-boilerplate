"""Event context models for the event system.

This module defines Pydantic models that represent the context/payload
for different types of events in the system.
"""

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class BaseEventContext(BaseModel):
    """Base event context with common fields."""

    timestamp: datetime = Field(default_factory=lambda: datetime.now(), description="Event timestamp")
    request_id: str | None = Field(default=None, description="Request ID for tracing")
    user_agent: str | None = Field(default=None, description="User agent string")
    ip_address: str | None = Field(default=None, description="Client IP address")


class LoginEventContext(BaseEventContext):
    """Context for user login events."""

    user_id: UUID = Field(..., description="User account ID")
    email: str = Field(..., description="User email address")
    name: str = Field(..., description="User display name")
    is_admin: bool = Field(default=False, description="Whether user is admin")
    remember_me: bool = Field(default=False, description="Whether remember me was selected")
    session_duration: int | None = Field(default=None, description="Session duration in seconds")


class LogoutEventContext(BaseEventContext):
    """Context for user logout events."""

    user_id: UUID = Field(..., description="User account ID")
    email: str = Field(..., description="User email address")
    session_duration: int | None = Field(default=None, description="Session duration in seconds")
    logout_reason: str = Field(default="user_initiated", description="Reason for logout")


class LoginFailedEventContext(BaseEventContext):
    """Context for failed login attempts."""

    email: str = Field(..., description="Attempted email address")
    failure_reason: str = Field(..., description="Reason for login failure")
    attempt_count: int | None = Field(default=None, description="Number of failed attempts")


class RegistrationEventContext(BaseEventContext):
    """Context for user registration events."""

    user_id: UUID = Field(..., description="New user account ID")
    email: str = Field(..., description="User email address")
    name: str = Field(..., description="User display name")
    account_status: str = Field(..., description="Initial account status")


class GenericEventContext(BaseEventContext):
    """Generic event context for custom events."""

    event_type: str = Field(..., description="Type of the event")
    data: dict[str, Any] = Field(default_factory=dict, description="Event-specific data")

"""Profile models for user profile management."""

from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID

from pydantic import BaseModel, Field

if TYPE_CHECKING:
    from ..models.auth import UserProfile


class ProfileUpdateRequest(BaseModel):
    """Request model for updating user profile."""

    name: str | None = Field(None, min_length=1, max_length=255, description="User display name")
    timezone: str | None = Field(None, max_length=50, description="User timezone (e.g., 'UTC', 'America/New_York')")
    avatar: str | None = Field(None, max_length=500, description="User avatar URL")

    class Config:
        json_schema_extra = {
            "example": {
                "name": "John Doe Updated",
                "timezone": "America/New_York",
                "avatar": "https://example.com/new-avatar.jpg",
            }
        }


class ProfileUpdateResponse(BaseModel):
    """Response model for profile update."""

    success: bool = Field(True, description="Profile update success status")
    message: str = Field("Profile updated successfully", description="Success message")
    user: "UserProfile" = Field(..., description="Updated user profile")
    updated_at: datetime = Field(..., description="Profile update timestamp")

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "message": "Profile updated successfully",
                "user": {
                    "id": "123e4567-e89b-12d3-a456-426614174000",
                    "name": "John Doe Updated",
                    "email": "john.doe@example.com",
                    "status": "ACTIVE",
                    "timezone": "America/New_York",
                    "avatar": "https://example.com/new-avatar.jpg",
                    "is_admin": False,
                    "last_login_at": "2024-01-15T10:30:00Z",
                    "initialized_at": "2024-01-01T00:00:00Z",
                    "created_at": "2024-01-01T00:00:00Z",
                },
                "updated_at": "2024-01-15T14:30:00Z",
            }
        }


class ProfileStatsResponse(BaseModel):
    """Response model for profile statistics."""

    user_id: UUID = Field(..., description="User unique identifier")
    account_age_days: int = Field(..., description="Number of days since account creation")
    last_login_days_ago: int | None = Field(None, description="Number of days since last login")
    is_recently_active: bool = Field(..., description="Whether user was active in the last 7 days")
    profile_completion: float = Field(..., description="Profile completion percentage (0.0 to 1.0)")
    missing_fields: list[str] = Field(default_factory=list, description="List of missing profile fields")

    class Config:
        json_schema_extra = {
            "example": {
                "user_id": "123e4567-e89b-12d3-a456-426614174000",
                "account_age_days": 45,
                "last_login_days_ago": 2,
                "is_recently_active": True,
                "profile_completion": 0.8,
                "missing_fields": ["avatar", "timezone"],
            }
        }


class ProfilePreferencesRequest(BaseModel):
    """Request model for updating user preferences."""

    timezone: str | None = Field(None, max_length=50, description="Preferred timezone")
    email_notifications: bool | None = Field(None, description="Enable email notifications")
    theme: str | None = Field(None, description="UI theme preference (light, dark, auto)")
    language: str | None = Field(None, max_length=10, description="Preferred language code (e.g., 'en', 'es')")

    class Config:
        json_schema_extra = {
            "example": {
                "timezone": "America/New_York",
                "email_notifications": True,
                "theme": "dark",
                "language": "en",
            }
        }


class ProfilePreferencesResponse(BaseModel):
    """Response model for profile preferences."""

    success: bool = Field(True, description="Preferences update success status")
    message: str = Field("Preferences updated successfully", description="Success message")
    preferences: dict = Field(..., description="Updated preferences")
    updated_at: datetime = Field(..., description="Preferences update timestamp")

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "message": "Preferences updated successfully",
                "preferences": {
                    "timezone": "America/New_York",
                    "email_notifications": True,
                    "theme": "dark",
                    "language": "en",
                },
                "updated_at": "2024-01-15T14:30:00Z",
            }
        }

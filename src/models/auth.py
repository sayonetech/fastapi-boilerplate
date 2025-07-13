"""Authentication models for login and session management."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field

from ..entities.status import AccountStatus


class LoginRequest(BaseModel):
    """Request model for user login."""

    email: EmailStr = Field(..., description="User email address")
    password: str = Field(..., min_length=1, description="User password")
    remember_me: bool = Field(default=False, description="Whether to remember the user for extended session")

    class Config:
        json_schema_extra = {
            "example": {
                "email": "admin@example.com",
                "password": "securepassword123",
                "remember_me": True,
            }  # pragma: allowlist secret
        }


class UserProfile(BaseModel):
    """User profile information for login response."""

    id: UUID = Field(..., description="User unique identifier")
    name: str = Field(..., description="User display name")
    email: EmailStr = Field(..., description="User email address")
    status: AccountStatus = Field(..., description="Account status")
    timezone: str | None = Field(None, description="User timezone")
    avatar: str | None = Field(None, description="User avatar URL")
    is_admin: bool = Field(..., description="Whether user has admin privileges")
    last_login_at: datetime | None = Field(None, description="Last login timestamp")
    initialized_at: datetime | None = Field(None, description="Account initialization timestamp")
    created_at: datetime = Field(..., description="Account creation timestamp")

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "name": "John Doe",
                "email": "john.doe@example.com",
                "status": "ACTIVE",
                "timezone": "UTC",
                "avatar": "https://example.com/avatar.jpg",
                "is_admin": False,
                "last_login_at": "2024-01-15T10:30:00Z",
                "initialized_at": "2024-01-01T00:00:00Z",
                "created_at": "2024-01-01T00:00:00Z",
            }
        }


class SessionInfo(BaseModel):
    """Session information for login response."""

    session_id: str = Field(..., description="Session identifier")
    expires_at: datetime = Field(..., description="Session expiration timestamp")
    remember_me: bool = Field(..., description="Whether session is extended")

    class Config:
        json_schema_extra = {
            "example": {
                "session_id": "sess_123e4567e89b12d3a456426614174000",
                "expires_at": "2024-01-16T10:30:00Z",
                "remember_me": True,
            }
        }


class LoginResponse(BaseModel):
    """Response model for successful login."""

    success: bool = Field(True, description="Login success status")
    message: str = Field("Login successful", description="Success message")
    user: UserProfile = Field(..., description="User profile information")
    session: SessionInfo = Field(..., description="Session information")
    login_at: datetime = Field(..., description="Login timestamp")
    login_ip: str | None = Field(None, description="Login IP address")

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "message": "Login successful",
                "user": {
                    "id": "123e4567-e89b-12d3-a456-426614174000",
                    "name": "John Doe",
                    "email": "john.doe@example.com",
                    "status": "ACTIVE",
                    "timezone": "UTC",
                    "avatar": None,
                    "is_admin": False,
                    "last_login_at": "2024-01-15T10:30:00Z",
                    "initialized_at": "2024-01-01T00:00:00Z",
                    "created_at": "2024-01-01T00:00:00Z",
                },
                "session": {
                    "session_id": "sess_123e4567e89b12d3a456426614174000",
                    "expires_at": "2024-01-16T10:30:00Z",
                    "remember_me": True,
                },
                "login_at": "2024-01-15T10:30:00Z",
                "login_ip": "192.168.1.100",
            }
        }


class LogoutRequest(BaseModel):
    """Request model for user logout."""

    session_id: str | None = Field(None, description="Session ID to logout (optional, can be inferred from headers)")

    class Config:
        json_schema_extra = {"example": {"session_id": "sess_123e4567e89b12d3a456426614174000"}}


class LogoutResponse(BaseModel):
    """Response model for logout."""

    success: bool = Field(True, description="Logout success status")
    message: str = Field("Logout successful", description="Success message")
    logged_out_at: datetime = Field(..., description="Logout timestamp")

    class Config:
        json_schema_extra = {
            "example": {"success": True, "message": "Logout successful", "logged_out_at": "2024-01-15T11:00:00Z"}
        }


class SessionValidationResponse(BaseModel):
    """Response model for session validation."""

    valid: bool = Field(..., description="Whether session is valid")
    user: UserProfile | None = Field(None, description="User profile if session is valid")
    session: SessionInfo | None = Field(None, description="Session info if valid")
    message: str = Field(..., description="Validation message")

    class Config:
        json_schema_extra = {
            "example": {
                "valid": True,
                "user": {
                    "id": "123e4567-e89b-12d3-a456-426614174000",
                    "name": "John Doe",
                    "email": "john.doe@example.com",
                    "status": "ACTIVE",
                    "timezone": "UTC",
                    "avatar": None,
                    "is_admin": False,
                    "last_login_at": "2024-01-15T10:30:00Z",
                    "initialized_at": "2024-01-01T00:00:00Z",
                    "created_at": "2024-01-01T00:00:00Z",
                },
                "session": {
                    "session_id": "sess_123e4567e89b12d3a456426614174000",
                    "expires_at": "2024-01-16T10:30:00Z",
                    "remember_me": True,
                },
                "message": "Session is valid",
            }
        }


class PasswordChangeRequest(BaseModel):
    """Request model for password change."""

    current_password: str = Field(..., min_length=1, description="Current password for verification")
    new_password: str = Field(..., min_length=8, description="New password (minimum 8 characters)")

    class Config:
        json_schema_extra = {
            "example": {"current_password": "oldpassword123", "new_password": "newstrongpassword456"}
        }  # pragma: allowlist secret


class PasswordChangeResponse(BaseModel):
    """Response model for password change."""

    success: bool = Field(True, description="Password change success status")
    message: str = Field("Password changed successfully", description="Success message")
    changed_at: datetime = Field(..., description="Password change timestamp")

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "message": "Password changed successfully",
                "changed_at": "2024-01-15T12:00:00Z",
            }
        }

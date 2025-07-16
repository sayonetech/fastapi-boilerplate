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


class UserProfile(BaseModel):
    """User profile information for login response."""

    model_config = {"from_attributes": True}

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


class SessionInfo(BaseModel):
    """Session information for login response."""

    session_id: str = Field(..., description="Session identifier")
    expires_at: datetime = Field(..., description="Session expiration timestamp")
    remember_me: bool = Field(..., description="Whether session is extended")


class LoginResponse(BaseModel):
    """Response model for successful login."""

    success: bool = Field(True, description="Login success status")
    message: str = Field("Login successful", description="Success message")
    user: UserProfile = Field(..., description="User profile information")
    session: SessionInfo = Field(..., description="Session information")
    login_at: datetime = Field(..., description="Login timestamp")
    login_ip: str | None = Field(None, description="Login IP address")


class LogoutRequest(BaseModel):
    """Request model for user logout."""

    session_id: str | None = Field(None, description="Session ID to logout (optional, can be inferred from headers)")


class LogoutResponse(BaseModel):
    """Response model for logout."""

    success: bool = Field(True, description="Logout success status")
    message: str = Field("Logout successful", description="Success message")
    logged_out_at: datetime = Field(..., description="Logout timestamp")


class SessionValidationResponse(BaseModel):
    """Response model for session validation."""

    valid: bool = Field(..., description="Whether session is valid")
    user: UserProfile | None = Field(None, description="User profile if session is valid")
    session: SessionInfo | None = Field(None, description="Session info if valid")
    message: str = Field(..., description="Validation message")


class PasswordChangeRequest(BaseModel):
    """Request model for password change."""

    current_password: str = Field(..., min_length=1, description="Current password for verification")
    new_password: str = Field(..., min_length=8, description="New password (minimum 8 characters)")


class PasswordChangeResponse(BaseModel):
    """Response model for password change."""

    success: bool = Field(True, description="Password change success status")
    message: str = Field("Password changed successfully", description="Success message")
    changed_at: datetime = Field(..., description="Password change timestamp")

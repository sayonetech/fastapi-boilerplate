"""Token models for JWT-based authentication."""

from pydantic import BaseModel, Field


class TokenPair(BaseModel):
    """Token pair containing access and refresh tokens."""

    access_token: str = Field(..., description="JWT access token")
    refresh_token: str = Field(..., description="JWT refresh token")
    token_type: str = Field(default="Bearer", description="Token type")
    expires_in: int = Field(..., description="Access token expiration time in seconds")
    refresh_expires_in: int = Field(..., description="Refresh token expiration time in seconds")


class LoginResponse(BaseModel):
    """Standard login response."""

    result: str = Field(default="success", description="Result status")
    data: TokenPair = Field(..., description="Token pair data")


class RegisterResponse(BaseModel):
    """Standard registration response."""

    result: str = Field(default="success", description="Result status")
    data: TokenPair = Field(..., description="Token pair data")


class RefreshTokenRequest(BaseModel):
    """Request model for token refresh."""

    refresh_token: str = Field(..., min_length=1, description="Refresh token")


class RefreshTokenResponse(BaseModel):
    """Response model for token refresh."""

    result: str = Field(default="success", description="Result status")
    data: TokenPair = Field(..., description="New token pair data")


class RegisterRequest(BaseModel):
    """Request model for user registration."""

    name: str = Field(..., min_length=1, max_length=255, description="User full name")
    email: str = Field(..., description="User email address")
    password: str = Field(..., min_length=8, max_length=128, description="User password")


class TokenClaims(BaseModel):
    """JWT token claims."""

    sub: str = Field(..., description="Subject (user ID)")
    email: str = Field(..., description="User email")
    name: str = Field(..., description="User name")
    is_admin: bool = Field(default=False, description="Admin status")
    iat: int = Field(..., description="Issued at timestamp")
    exp: int = Field(..., description="Expiration timestamp")
    jti: str = Field(..., description="JWT ID")
    token_type: str = Field(..., description="Token type (access/refresh)")


class ErrorResponse(BaseModel):
    """Standard error response."""

    result: str = Field(default="error", description="Result status")
    message: str = Field(..., description="Error message")
    code: str | None = Field(None, description="Error code")

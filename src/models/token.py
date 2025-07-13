"""Token models for JWT-based authentication."""

from pydantic import BaseModel, Field


class TokenPair(BaseModel):
    """Token pair containing access and refresh tokens."""

    access_token: str = Field(..., description="JWT access token")
    refresh_token: str = Field(..., description="JWT refresh token")
    token_type: str = Field(default="Bearer", description="Token type")
    expires_in: int = Field(..., description="Access token expiration time in seconds")
    refresh_expires_in: int = Field(..., description="Refresh token expiration time in seconds")

    class Config:
        json_schema_extra = {
            "example": {
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "token_type": "Bearer",
                "expires_in": 3600,
                "refresh_expires_in": 2592000,
            }
        }


class LoginResponse(BaseModel):
    """Standard login response."""

    result: str = Field(default="success", description="Result status")
    data: TokenPair = Field(..., description="Token pair data")

    class Config:
        json_schema_extra = {
            "example": {
                "result": "success",
                "data": {
                    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                    "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                    "token_type": "Bearer",
                    "expires_in": 3600,
                    "refresh_expires_in": 2592000,
                },
            }
        }


class RegisterResponse(BaseModel):
    """Standard registration response."""

    result: str = Field(default="success", description="Result status")
    data: TokenPair = Field(..., description="Token pair data")

    class Config:
        json_schema_extra = {
            "example": {
                "result": "success",
                "data": {
                    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                    "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                    "token_type": "Bearer",
                    "expires_in": 3600,
                    "refresh_expires_in": 2592000,
                },
            }
        }


class RefreshTokenRequest(BaseModel):
    """Request model for token refresh."""

    refresh_token: str = Field(..., description="Refresh token")

    class Config:
        json_schema_extra = {"example": {"refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."}}


class RefreshTokenResponse(BaseModel):
    """Response model for token refresh."""

    result: str = Field(default="success", description="Result status")
    data: TokenPair = Field(..., description="New token pair data")

    class Config:
        json_schema_extra = {
            "example": {
                "result": "success",
                "data": {
                    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                    "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                    "token_type": "Bearer",
                    "expires_in": 3600,
                    "refresh_expires_in": 2592000,
                },
            }
        }


class RegisterRequest(BaseModel):
    """Request model for user registration."""

    name: str = Field(..., min_length=1, max_length=255, description="User full name")
    email: str = Field(..., description="User email address")
    password: str = Field(..., min_length=8, max_length=128, description="User password")

    class Config:
        json_schema_extra = {
            "example": {
                "name": "John Doe",
                "email": "john.doe@example.com",
                "password": "securepassword123",
            }  # pragma: allowlist secret
        }


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

    class Config:
        json_schema_extra = {
            "example": {
                "sub": "123e4567-e89b-12d3-a456-426614174000",
                "email": "john.doe@example.com",
                "name": "John Doe",
                "is_admin": False,
                "iat": 1640995200,
                "exp": 1640998800,
                "jti": "abc123def456",  # pragma: allowlist secret
                "token_type": "access",
            }
        }


class ErrorResponse(BaseModel):
    """Standard error response."""

    result: str = Field(default="error", description="Result status")
    message: str = Field(..., description="Error message")
    code: str | None = Field(None, description="Error code")

    class Config:
        json_schema_extra = {
            "example": {"result": "error", "message": "Invalid credentials", "code": "INVALID_CREDENTIALS"}
        }

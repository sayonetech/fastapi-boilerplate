"""Pydantic models for rate limiting responses and data structures."""

from pydantic import BaseModel, Field


class RateLimitInfo(BaseModel):
    """Information about current rate limit status."""

    is_limited: bool = Field(description="Whether the request is currently rate limited")

    remaining_attempts: int = Field(description="Number of attempts remaining before rate limiting", ge=0)

    max_attempts: int = Field(description="Maximum number of attempts allowed", gt=0)

    time_window: int = Field(description="Time window in seconds for rate limiting", gt=0)

    time_until_reset: int | None = Field(
        description="Seconds until rate limit resets, null if not limited", ge=0, default=None
    )


class RateLimitExceededResponse(BaseModel):
    """Response model for rate limit exceeded errors."""

    result: str = Field(default="error", description="Result status")

    message: str = Field(description="Human-readable error message")

    error_code: str = Field(default="RATE_LIMIT_EXCEEDED", description="Machine-readable error code")

    rate_limit_info: RateLimitInfo = Field(description="Details about the rate limit")

    retry_after: int = Field(description="Seconds to wait before retrying", gt=0)


class RateLimitHeaders(BaseModel):
    """HTTP headers for rate limiting information."""

    x_ratelimit_limit: int = Field(description="Maximum number of requests allowed", alias="X-RateLimit-Limit")

    x_ratelimit_remaining: int = Field(
        description="Number of requests remaining in current window", alias="X-RateLimit-Remaining"
    )

    x_ratelimit_reset: int | None = Field(
        description="Unix timestamp when rate limit resets", alias="X-RateLimit-Reset", default=None
    )

    retry_after: int | None = Field(description="Seconds to wait before retrying", alias="Retry-After", default=None)

    class Config:
        populate_by_name = True
        allow_population_by_field_name = True

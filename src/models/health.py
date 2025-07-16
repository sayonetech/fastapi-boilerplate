"""Health check models."""

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    """Health check response model."""

    status: str = Field(..., description="Health status of the service")
    message: str = Field(..., description="Human-readable status message")
    version: str = Field(..., description="Current version of the service")

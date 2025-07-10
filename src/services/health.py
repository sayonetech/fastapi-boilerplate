"""Health check service."""

import logging
from typing import Annotated

from fastapi import Depends

from ..extensions.ext_db import db_engine
from ..models.health import HealthResponse

log = logging.getLogger(__name__)


class HealthService:
    """Service for health check operations."""

    def __init__(self) -> None:
        """Initialize the health service."""
        self.version = "0.1.0"

    async def get_health_status(self) -> HealthResponse:
        """Get general health status with database check."""
        log.info("Health check: general status requested.")

        # Check database health
        db_healthy = db_engine.is_healthy()

        if not db_healthy:
            log.warning("Health check: database is unhealthy")
            return HealthResponse(
                status="unhealthy",
                message="Database connection failed",
                version=self.version,
            )

        return HealthResponse(
            status="healthy",
            message="Service is running normally",
            version=self.version,
        )

    async def get_readiness_status(self) -> HealthResponse:
        """Get readiness status for Kubernetes readiness probe."""
        log.info("Health check: readiness probe requested.")

        # Check if database is ready
        db_healthy = db_engine.is_healthy()

        if not db_healthy:
            log.warning("Readiness check: database is not ready")
            return HealthResponse(
                status="not_ready",
                message="Database is not ready",
                version=self.version,
            )

        return HealthResponse(
            status="ready",
            message="Service is ready to receive traffic",
            version=self.version,
        )

    async def get_liveness_status(self) -> HealthResponse:
        """Get liveness status for Kubernetes liveness probe."""
        # Add any liveness checks here
        return HealthResponse(
            status="alive",
            message="Service is alive and responsive",
            version=self.version,
        )


def get_health_service() -> HealthService:
    """Dependency to get health service instance."""
    return HealthService()


# Type alias for dependency injection
HealthServiceDep = Annotated[HealthService, Depends(get_health_service)]

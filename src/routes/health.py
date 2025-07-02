"""Health check routes."""

from fastapi import APIRouter, HTTPException

from ..models.health import HealthResponse
from ..services.health import HealthServiceDep

health_router = APIRouter()


@health_router.get("/", response_model=HealthResponse, operation_id="get_health_status")
async def health_check(
    health_service: HealthServiceDep,
) -> HealthResponse:
    """Get application health status."""
    try:
        return await health_service.get_health_status()
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Health check failed: {str(e)}",
        ) from e


@health_router.get("/ready", response_model=HealthResponse)
async def readiness_check(
    health_service: HealthServiceDep,
) -> HealthResponse:
    """Get application readiness status."""
    try:
        return await health_service.get_readiness_status()
    except Exception as e:
        raise HTTPException(
            status_code=503,
            detail=f"Readiness check failed: {str(e)}",
        ) from e


@health_router.get("/live", response_model=HealthResponse)
async def liveness_check(
    health_service: HealthServiceDep,
) -> HealthResponse:
    """Get application liveness status."""
    try:
        return await health_service.get_liveness_status()
    except Exception as e:
        raise HTTPException(
            status_code=503,
            detail=f"Liveness check failed: {str(e)}",
        ) from e

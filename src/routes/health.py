"""Health check routes - class-based version."""

from fastapi import APIRouter, HTTPException, Depends
from ..models.health import HealthResponse
from ..services.health import HealthServiceDep


class HealthRouter:
    def __init__(self):
        self.router = APIRouter()
        self.router.add_api_route(
            "/", self.health_check, response_model=HealthResponse, methods=["GET"], operation_id="get_health_status"
        )
        self.router.add_api_route(
            "/ready", self.readiness_check, response_model=HealthResponse, methods=["GET"]
        )
        self.router.add_api_route(
            "/live", self.liveness_check, response_model=HealthResponse, methods=["GET"]
        )

    async def _handle_check(self, fn, status_code: int, label: str):
        """
        Shared helper to wrap service calls with exception handling.
        """
        try:
            return await fn()
        except Exception as e:
            raise HTTPException(
                status_code=status_code,
                detail=f"{label} check failed: {str(e)}",
            ) from e

    async def health_check(self, health_service: HealthServiceDep = Depends()) -> HealthResponse:
        return await self._handle_check(health_service.get_health_status, 500, "Health")

    async def readiness_check(self, health_service: HealthServiceDep = Depends()) -> HealthResponse:
        return await self._handle_check(health_service.get_readiness_status, 503, "Readiness")

    async def liveness_check(self, health_service: HealthServiceDep = Depends()) -> HealthResponse:
        return await self._handle_check(health_service.get_liveness_status, 503, "Liveness")


# Expose the router instance to be imported elsewhere (e.g., in main.py)
health_router = HealthRouter().router

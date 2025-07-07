"""Routes package with centralized registration."""

from fastapi import FastAPI

from .health import health_router


def register_routes(app: FastAPI) -> None:
    """
    Register all route modules with the FastAPI application.

    Args:
        app (FastAPI): The FastAPI application instance
    """
    # Health routes
    app.include_router(health_router, prefix="/api/v1/health", tags=["health"])


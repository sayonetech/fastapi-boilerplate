"""Routes package with centralized registration."""

from fastapi import FastAPI

from .health import health_router
from .locations import locations_router


def register_routes(app: FastAPI) -> None:
    """
    Register all route modules with the FastAPI application.

    Args:
        app (FastAPI): The FastAPI application instance
    """
    # Health routes
    app.include_router(health_router, prefix="/api/v1/health", tags=["health"])

    # Locations routes
    app.include_router(locations_router, prefix="/locations", tags=["locations"])



    # Add more route registrations here as you create new modules
    # Example:
    # from .users import user_router
    # app.include_router(user_router, prefix="/api/v1/users", tags=["users"])

    # from .auth import auth_router
    # app.include_router(auth_router, prefix="/api/v1/auth", tags=["auth"])

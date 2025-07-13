"""Protection middleware for enforcing authentication on protected routes."""

import logging
from typing import Any, cast

from fastapi import HTTPException, Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)


class ProtectionMiddleware(BaseHTTPMiddleware):
    """
    Middleware to enforce authentication on protected routes.

    This middleware checks if a route requires protection based on
    controller-level and method-level annotations, and enforces
    authentication accordingly.
    """

    def __init__(self, app, exclude_paths: list[str] | None = None):
        """
        Initialize the protection middleware.

        Args:
            app: FastAPI application instance
            exclude_paths: List of paths to exclude from protection checks
        """
        super().__init__(app)
        self.exclude_paths = exclude_paths or [
            "/docs",
            "/redoc",
            "/openapi.json",
            "/favicon.ico",
            "/health",
            "/api/v1/health",
        ]
        logger.info("Protection middleware initialized")

    async def dispatch(self, request: Request, call_next) -> Response:
        """
        Process the request and enforce protection if required.

        Args:
            request: The incoming request
            call_next: The next middleware/handler in the chain

        Returns:
            Response from the next handler

        Raises:
            HTTPException: If authentication is required but not provided
        """
        # Skip protection for excluded paths
        if self._should_skip_protection(request):
            response = await call_next(request)
            return cast(Response, response)

        # Check if route requires protection
        if await self._requires_protection(request):
            # Enforce authentication
            await self._enforce_authentication(request)

        # Continue to the next middleware/handler
        response = await call_next(request)
        return cast(Response, response)

    def _should_skip_protection(self, request: Request) -> bool:
        """
        Check if protection should be skipped for this request.

        Args:
            request: The incoming request

        Returns:
            True if protection should be skipped, False otherwise
        """
        path = request.url.path

        # Skip excluded paths
        for exclude_path in self.exclude_paths:
            if path.startswith(exclude_path):
                logger.debug(f"Skipping protection for excluded path: {path}")
                return True

        # Skip OPTIONS requests (CORS preflight)
        if request.method == "OPTIONS":
            logger.debug(f"Skipping protection for OPTIONS request: {path}")
            return True

        return False

    async def _requires_protection(self, request: Request) -> bool:
        """
        Check if the current route requires protection.

        Args:
            request: The incoming request

        Returns:
            True if protection is required, False otherwise
        """
        try:
            from ..routes.protection import get_route_protection_info

            path = request.url.path
            method = request.method.upper()

            # Get protection info for this route
            protection_info = get_route_protection_info(path, method)

            if not protection_info:
                logger.debug(f"No protection info found for {method} {path}")
                return False

            controller_class = protection_info["controller_class"]
            method_name = protection_info["method_name"]

            # Get the actual method from the controller
            if hasattr(controller_class, method_name):
                from ..routes.protection import is_method_protected

                method_obj = getattr(controller_class, method_name)
                is_protected = is_method_protected(method_obj, controller_class)

                logger.debug(f"Route {method} {path} protection required: {is_protected}")
                return is_protected

            return False

        except ImportError:
            logger.warning("Protection system not available")
            return False
        except Exception:
            logger.exception("Error checking route protection")
            return False

    async def _enforce_authentication(self, request: Request) -> None:
        """
        Enforce authentication for the current request.

        Args:
            request: The incoming request

        Raises:
            HTTPException: If authentication fails
        """
        try:
            # Check if login is disabled (for testing)
            from ..configs import madcrow_config

            if getattr(madcrow_config, "LOGIN_DISABLED", False):
                logger.debug("Login disabled, skipping authentication check")
                return

            # Use the existing authentication system
            from ..dependencies.auth import (
                get_auth_service_dep,
                get_current_user_from_jwt_required,
            )
            from ..dependencies.db import get_session

            # Get dependencies manually
            db_session = next(get_session())
            try:
                auth_service = get_auth_service_dep(db_session)

                # This will raise HTTPException if user is not authenticated
                current_user = get_current_user_from_jwt_required(request, auth_service)

                if not current_user:
                    logger.warning(f"Authentication failed for {request.method} {request.url.path}")
                    raise HTTPException(status_code=401, detail="Authentication required")

                # Store user in request state for downstream use
                request.state.current_user = current_user
                logger.debug(f"Authentication successful for user: {current_user.email}")

            finally:
                db_session.close()

        except HTTPException:
            # Re-raise HTTP exceptions (authentication failures)
            raise
        except Exception as e:
            logger.exception("Unexpected error during authentication")
            raise HTTPException(status_code=500, detail="Authentication system error") from e

    def get_protection_status(self) -> dict[str, Any]:
        """
        Get the current protection status and statistics.

        Returns:
            Dictionary containing protection middleware status
        """
        try:
            from ..routes.protection import get_all_protected_routes

            protected_routes = get_all_protected_routes()

            return {
                "middleware_active": True,
                "excluded_paths": self.exclude_paths,
                "protected_routes_count": len(protected_routes),
                "protected_routes": list(protected_routes.keys()),
            }

        except ImportError:
            return {
                "middleware_active": True,
                "excluded_paths": self.exclude_paths,
                "protected_routes_count": 0,
                "protected_routes": [],
                "error": "Protection system not available",
            }
        except Exception as e:
            return {
                "middleware_active": True,
                "excluded_paths": self.exclude_paths,
                "error": f"Error getting protection status: {e}",
            }


def create_protection_middleware(exclude_paths: list[str] | None = None) -> type[ProtectionMiddleware]:
    """
    Create a protection middleware class with custom configuration.

    Args:
        exclude_paths: List of paths to exclude from protection checks

    Returns:
        Configured ProtectionMiddleware class
    """

    class ConfiguredProtectionMiddleware(ProtectionMiddleware):
        def __init__(self, app):
            super().__init__(app, exclude_paths=exclude_paths)

    return ConfiguredProtectionMiddleware


# Default middleware instance
def get_default_protection_middleware() -> type[ProtectionMiddleware]:
    """Get the default protection middleware with standard exclusions."""
    return create_protection_middleware(
        exclude_paths=[
            "/docs",
            "/redoc",
            "/openapi.json",
            "/favicon.ico",
            "/health",
            "/api/v1/health",
            "/api/v1/security/info",  # Allow security info endpoint
        ]
    )

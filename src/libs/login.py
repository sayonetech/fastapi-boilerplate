"""Login required decorator for FastAPI routes."""

import logging
from collections.abc import Callable
from functools import wraps
from typing import Any

from fastapi import HTTPException, Request

from ..configs import madcrow_config

logger = logging.getLogger(__name__)


def login_required(func: Callable[..., Any]) -> Callable[..., Any]:
    """
    Decorator to ensure that the current user is logged in and authenticated.

    This decorator checks for a valid JWT token in the request headers
    and validates the user before allowing access to the decorated endpoint.

    Similar to Dify's login_required decorator but adapted for FastAPI.
    This is a simpler alternative to using CurrentUser dependency injection.

    Usage:
        @login_required
        async def my_endpoint(request: Request) -> dict:
            # User is guaranteed to be authenticated here
            return {"message": "success"}

    Args:
        func: The view function to decorate

    Returns:
        Decorated function that requires authentication

    Raises:
        HTTPException: If user is not authenticated (401)
    """

    # Mark function as requiring login for the protection system
    func._login_required = True

    @wraps(func)
    async def decorated_view(*args, **kwargs) -> Any:
        # Check if login is disabled (for testing)
        if getattr(madcrow_config, "LOGIN_DISABLED", False):
            logger.debug("Login disabled, skipping authentication check")
            return await func(*args, **kwargs)

        # Extract request from args/kwargs
        request: Request | None = None

        # Look for Request object in args (for class methods, self is first)
        for arg in args:
            if isinstance(arg, Request):
                request = arg
                break

        # Look for Request object in kwargs
        if not request:
            for _key, value in kwargs.items():
                if isinstance(value, Request):
                    request = value
                    break

        if not request:
            logger.error("No Request object found in function arguments")
            raise HTTPException(status_code=500, detail="Internal server error: Request object not found")

        try:
            # Use existing authentication dependency to validate user
            # This will raise HTTPException if authentication fails
            from ..dependencies.auth import (
                get_auth_service_dep,
                get_current_user_from_jwt_required,
            )
            from ..dependencies.db import get_session

            # Get dependencies manually
            db_session = next(get_session())
            auth_service = get_auth_service_dep(db_session)

            try:
                # This will raise HTTPException if user is not authenticated
                current_user = get_current_user_from_jwt_required(request, auth_service)

                logger.debug(f"Authenticated user {current_user.email} for {request.url.path}")

                # Call the original function
                return await func(*args, **kwargs)

            finally:
                # Clean up database session
                db_session.close()

        except HTTPException:
            # Re-raise HTTP exceptions (like 401)
            raise
        except Exception as e:
            logger.exception(f"Error in login_required decorator for {request.url.path}")
            raise HTTPException(status_code=500, detail="Authentication service error") from e

    return decorated_view


def admin_required(func: Callable[..., Any]) -> Callable[..., Any]:
    """
    Decorator to ensure that the current user is logged in and has admin privileges.

    This decorator first checks authentication (like login_required) and then
    verifies that the user has admin privileges.

    Usage:
        @admin_required
        async def admin_endpoint(request: Request) -> dict:
            # User is guaranteed to be authenticated and admin here
            return {"message": "admin access granted"}

    Args:
        func: The view function to decorate

    Returns:
        Decorated function that requires admin authentication

    Raises:
        HTTPException: If user is not authenticated (401) or not admin (403)
    """

    @wraps(func)
    async def decorated_view(*args, **kwargs) -> Any:
        # Check if login is disabled (for testing)
        if getattr(madcrow_config, "LOGIN_DISABLED", False):
            logger.debug("Login disabled, skipping authentication check")
            return await func(*args, **kwargs)

        # Extract request from args/kwargs
        request: Request | None = None

        # Look for Request object in args (for class methods, self is first)
        for arg in args:
            if isinstance(arg, Request):
                request = arg
                break

        # Look for Request object in kwargs
        if not request:
            for _key, value in kwargs.items():
                if isinstance(value, Request):
                    request = value
                    break

        if not request:
            logger.error("No Request object found in function arguments")
            raise HTTPException(status_code=500, detail="Internal server error: Request object not found")

        try:
            # Use existing authentication dependency to validate user
            from ..dependencies.auth import (
                get_auth_service_dep,
                get_current_user_from_jwt_required,
            )
            from ..dependencies.db import get_session

            # Get dependencies manually
            db_session = next(get_session())
            auth_service = get_auth_service_dep(db_session)

            try:
                # This will raise HTTPException if user is not authenticated
                current_user = get_current_user_from_jwt_required(request, auth_service)

                # Check admin privileges
                if not current_user.is_admin:
                    logger.warning(f"Non-admin user {current_user.email} attempted to access admin endpoint")
                    raise HTTPException(status_code=403, detail="Admin privileges required")

                logger.debug(f"Admin user {current_user.email} accessing admin endpoint")

                # Call the original function
                return await func(*args, **kwargs)

            finally:
                # Clean up database session
                db_session.close()

        except HTTPException:
            # Re-raise HTTP exceptions (like 401, 403)
            raise
        except Exception as e:
            logger.exception(f"Error in admin_required decorator for {request.url.path}")
            raise HTTPException(status_code=500, detail="Authentication service error") from e

    return decorated_view

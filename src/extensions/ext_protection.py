"""Protection middleware extension for class-level and method-level authentication."""

import logging
from typing import Any

from ..beco_app import BecoApp
from ..configs import madcrow_config

logger = logging.getLogger(__name__)


def init_app(app: BecoApp) -> None:
    """
    Initialize protection middleware for the application.

    This extension adds the protection middleware that enforces authentication
    on routes based on controller-level and method-level annotations.

    Args:
        app: FastAPI application instance
    """
    try:
        logger.info("Initializing protection middleware...")

        # Import middleware
        from ..middleware.protection_middleware import get_default_protection_middleware

        # Get configured middleware class
        ProtectionMiddlewareClass = get_default_protection_middleware()

        # Add middleware to the application
        app.add_middleware(ProtectionMiddlewareClass)

        # Log protection status
        _log_protection_status(app)

        logger.info("Protection middleware initialized successfully")

    except Exception:
        logger.exception("Failed to initialize protection middleware")
        raise


def _log_protection_status(app: BecoApp) -> None:
    """
    Log the current protection status for debugging.

    Args:
        app: FastAPI application instance
    """
    try:
        from ..routes.protection import get_all_protected_routes

        protected_routes = get_all_protected_routes()

        logger.debug("Protection Middleware Configuration:")
        logger.debug(f"  Environment: {madcrow_config.DEPLOY_ENV}")
        logger.debug(f"  Debug Mode: {madcrow_config.DEBUG}")
        logger.debug(f"  Login Disabled: {getattr(madcrow_config, 'LOGIN_DISABLED', False)}")
        logger.debug(f"  Protected Routes Count: {len(protected_routes)}")

        if madcrow_config.DEBUG and protected_routes:
            logger.debug("  Protected Routes:")
            for route_key, route_info in protected_routes.items():
                controller_name = route_info.get("controller_name", "Unknown")
                method_name = route_info.get("method_name", "unknown")
                logger.debug(f"    {route_key} -> {controller_name}.{method_name}")

    except Exception as e:
        logger.warning(f"Failed to log protection status: {e}")


def get_protection_status() -> dict[str, Any]:
    """
    Get the current protection status and statistics.

    Returns:
        Dictionary containing protection system status
    """
    try:
        from ..routes.protection import get_all_protected_routes

        protected_routes = get_all_protected_routes()

        return {
            "extension_active": True,
            "environment": madcrow_config.DEPLOY_ENV,
            "debug_mode": madcrow_config.DEBUG,
            "login_disabled": getattr(madcrow_config, "LOGIN_DISABLED", False),
            "protected_routes_count": len(protected_routes),
            "protected_routes": {
                route_key: {
                    "controller": route_info.get("controller_name"),
                    "method": route_info.get("method_name"),
                }
                for route_key, route_info in protected_routes.items()
            },
        }

    except Exception as e:
        return {
            "extension_active": False,
            "error": str(e),
        }


# Cleanup function (if needed)
def cleanup() -> None:
    """Clean up protection middleware resources."""
    try:
        from ..routes.protection import clear_route_registry

        clear_route_registry()
        logger.debug("Protection middleware cleanup completed")

    except Exception as e:
        logger.warning(f"Error during protection middleware cleanup: {e}")

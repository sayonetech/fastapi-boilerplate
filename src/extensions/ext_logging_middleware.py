"""Logging middleware extension for FastAPI application."""

import logging

from ..beco_app import BecoApp
from ..configs import madcrow_config
from ..middleware.logging_middleware import RequestLoggingMiddleware

log = logging.getLogger(__name__)


def is_enabled() -> bool:
    """Check if logging middleware should be enabled."""
    # Could be made configurable in the future
    return True


def init_app(app: BecoApp) -> None:
    """Initialize request logging middleware with proper configuration."""
    try:
        log.info("Initializing request logging middleware...")

        # Add request logging middleware
        app.add_middleware(RequestLoggingMiddleware)

        # Log configuration in debug mode
        if madcrow_config.DEBUG:
            _log_middleware_config()

        log.info("Request logging middleware initialized successfully")

    except Exception:
        log.exception("Failed to initialize request logging middleware")
        raise


def _log_middleware_config() -> None:
    """Log current logging middleware configuration for debugging."""
    log.debug("Request Logging Middleware Configuration:")
    log.debug(f"  Environment: {madcrow_config.DEPLOY_ENV}")
    log.debug(f"  Debug Mode: {madcrow_config.DEBUG}")
    log.debug(f"  Log Level: {madcrow_config.LOG_LEVEL}")
    log.debug("  Features: Request/Response logging, Performance metrics, Error tracking")


def get_middleware_info() -> dict:
    """Get current logging middleware configuration info."""
    return {
        "middleware_enabled": True,
        "environment": madcrow_config.DEPLOY_ENV,
        "debug_mode": madcrow_config.DEBUG,
        "log_level": madcrow_config.LOG_LEVEL,
        "features": ["request_logging", "response_logging", "performance_metrics", "error_tracking"],
    }

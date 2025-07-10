"""Error handling extension for FastAPI application."""

import logging

from ..beco_app import BecoApp
from ..configs import madcrow_config
from ..middleware.error_middleware import ErrorHandlingMiddleware, create_error_handlers

logger = logging.getLogger(__name__)


def init_app(app: BecoApp) -> None:
    """
    Initialize enhanced error handling for the FastAPI application.

    This function sets up:
    1. Error handling middleware for consistent error responses
    2. Specific exception handlers for different error types
    3. Proper logging configuration for errors

    Args:
        app: FastAPI application instance
    """
    try:
        logger.info("Initializing enhanced error handling...")

        # Add error handling middleware
        # Note: This should be added early in the middleware stack
        app.add_middleware(
            ErrorHandlingMiddleware,
            include_debug_info=madcrow_config.DEBUG,
        )

        # Register specific exception handlers
        error_handlers = create_error_handlers()
        for exception_type, handler in error_handlers.items():
            app.add_exception_handler(exception_type, handler)

        # Log configuration in debug mode
        if madcrow_config.DEBUG:
            _log_error_handling_config()

        logger.info("Enhanced error handling initialized successfully")

    except Exception as e:
        logger.exception("Failed to initialize error handling")
        raise RuntimeError(f"Error handling initialization failed: {e}") from e


def _log_error_handling_config() -> None:
    """Log error handling configuration for debugging."""
    config_info = {
        "debug_mode": madcrow_config.DEBUG,
        "environment": madcrow_config.DEPLOY_ENV,
        "log_level": madcrow_config.LOG_LEVEL,
        "include_debug_info": madcrow_config.DEBUG,
    }

    logger.debug("Error handling configuration:", extra=config_info)

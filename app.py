"""Main FastAPI application for Madcrow Backend."""

import logging
import time

from fastapi import Request
from fastapi.responses import JSONResponse

from src.beco_app import BecoApp
from src.configs import madcrow_config
from src.lifespan_manager import LifespanManager
from src.routes import register_routes


def create_fast_api_app_with_configs() -> BecoApp:
    """
    Create the FastAPI application for Madcrow Backend
    with configs loaded from .env file.
    """
    app_name = madcrow_config.APP_NAME
    app_version = madcrow_config.APP_VERSION

    # Only enable documentation in development mode
    is_development = madcrow_config.DEPLOY_ENV == "DEVELOPMENT" and madcrow_config.DEBUG
    enable_swagger = is_development
    enable_redoc = is_development

    lifespan_manager = LifespanManager()

    async def setup_database():
        logging.info("Setting up Madcrow database...")

    async def cleanup_database():
        logging.info("Cleaning up Madcrow database...")
        # Import here to avoid circular imports
        from src.extensions.ext_db import cleanup

        cleanup()

    async def cleanup_redis():
        logging.info("Cleaning up Redis connections...")
        # Import here to avoid circular imports
        from src.extensions.ext_redis import cleanup

        cleanup()

    async def stop_background_tasks():
        logging.info("Stopping background tasks...")

    lifespan_manager.add_startup_task(setup_database)
    lifespan_manager.add_shutdown_task(stop_background_tasks)
    lifespan_manager.add_shutdown_task(cleanup_redis)
    lifespan_manager.add_shutdown_task(cleanup_database)

    beco_app = BecoApp(
        title=app_name,
        description="Madcrow Backend",
        version=app_version,
        docs_url="/docs" if enable_swagger else None,
        redoc_url="/redoc" if enable_redoc else None,
        lifespan=lifespan_manager.lifespan,
    )

    return beco_app


async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Global handler for unhandled exceptions."""

    logging.exception("Unhandled exception caught", exc_info=True, extra={"error": str(exc)})

    return JSONResponse(
        status_code=500,
        content={"detail": "An internal server error occurred."},
    )


def create_app() -> BecoApp:
    """Create and configure the FastAPI application for Madcrow Backend."""
    start_time = time.perf_counter()
    app = create_fast_api_app_with_configs()

    # Note: Exception handling is now managed by ext_error_handling extension
    # app.add_exception_handler(Exception, unhandled_exception_handler)

    register_routes(app)
    initialize_extensions(app)

    end_time = time.perf_counter()
    if madcrow_config.DEBUG:
        logging.info(f"Finished create_app ({round((end_time - start_time) * 1000, 2)} ms)")
    return app


def initialize_extensions(app: BecoApp):
    from src.extensions import (
        ext_compress,
        ext_cors,
        ext_db,
        ext_error_handling,
        ext_logging,
        ext_logging_middleware,
        ext_protection,
        ext_redis,
        ext_security,
        ext_set_secretkey,
        ext_timezone,
        ext_warnings,
    )

    extensions = [
        ext_logging,
        ext_error_handling,  # Error handling should be initialized early
        ext_logging_middleware,  # Request logging middleware
        ext_security,  # Security headers should be added early
        ext_cors,
        ext_compress,
        ext_set_secretkey,
        ext_timezone,
        ext_warnings,
        ext_db,
        ext_redis,  # Redis should be initialized after database
        ext_protection,  # Protection middleware should be initialized after routes are registered
    ]

    for ext in extensions:
        short_name = ext.__name__.split(".")[-1]
        is_enabled = ext.is_enabled() if hasattr(ext, "is_enabled") else True
        if not is_enabled:
            if madcrow_config.DEBUG:
                logging.info(f"Skipped {short_name}")
            continue

        start_time = time.perf_counter()
        ext.init_app(app)
        end_time = time.perf_counter()
        if madcrow_config.DEBUG:
            logging.info(f"Loaded {short_name} ({round((end_time - start_time) * 1000, 2)} ms)")

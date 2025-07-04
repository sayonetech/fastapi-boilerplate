"""Main FastAPI application for Madcrow Backend."""

import time
import logging
from fastapi import Request
from fastapi.responses import JSONResponse

from src.beco_app import BecoApp
from src.configs import madcrow_config
from src.lifespan_manager import LifespanManager
from src.middleware.logging_middleware import StructuredLoggingMiddleware
from src.routes import register_routes

log = logging.getLogger(__name__)


def create_fast_api_app_with_configs() -> BecoApp:
    """
    Create the FastAPI application for Madcrow Backend
    with configs loaded from .env file.
    """
    app_name = madcrow_config.APP_NAME
    app_version = madcrow_config.APP_VERSION
    enable_swagger = madcrow_config.DEPLOY_ENV == "DEVELOPMENT"
    enable_redoc = madcrow_config.DEPLOY_ENV == "DEVELOPMENT"
    debug = madcrow_config.DEBUG

    lifespan_manager = LifespanManager()

    async def setup_database():
        print("Setting up Madcrow database...")

    async def cleanup_database():
        print("Cleaning up Madcrow database...")

    async def stop_background_tasks():
        print("Stopping background tasks...")

    lifespan_manager.add_startup_task(setup_database)
    lifespan_manager.add_shutdown_task(stop_background_tasks)
    lifespan_manager.add_shutdown_task(cleanup_database)

    beco_app = BecoApp(
        title=app_name,
        description="Madcrow Backend",
        version=app_version,
        docs_url="/docs" if enable_swagger and debug else None,
        redoc_url="/redoc" if enable_redoc and debug else None,
        lifespan=lifespan_manager.lifespan,
    )

    return beco_app


async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Global handler for unhandled exceptions."""
    log.exception(
        "Unhandled exception caught",
        error=str(exc),
        exc_info=True,
    )
    return JSONResponse(
        status_code=500,
        content={"detail": "An internal server error occurred."},
    )


def create_app() -> BecoApp:
    """Create and configure the FastAPI application for Madcrow Backend."""
    start_time = time.perf_counter()
    app = create_fast_api_app_with_configs()

    app.add_middleware(StructuredLoggingMiddleware)
    app.add_exception_handler(Exception, unhandled_exception_handler)

    register_routes(app)
    initialize_extensions(app)

    end_time = time.perf_counter()
    if madcrow_config.DEBUG:
        log.info(f"Finished create_app ({round((end_time - start_time) * 1000, 2)} ms)")
    return app


def initialize_extensions(app: BecoApp):
    from src.extensions import ext_compress, ext_cors, ext_set_secretkey, ext_timezone, ext_warnings, ext_logging

    extensions = [
        ext_logging,
        ext_cors,
        ext_compress,
        ext_set_secretkey,
        ext_timezone,
        ext_warnings,
    ]

    for ext in extensions:
        short_name = ext.__name__.split(".")[-1]
        is_enabled = ext.is_enabled() if hasattr(ext, "is_enabled") else True
        if not is_enabled:
            if madcrow_config.DEBUG:
                log.info(f"Skipped {short_name}")
            continue

        start_time = time.perf_counter()
        ext.init_app(app)
        end_time = time.perf_counter()
        if madcrow_config.DEBUG:
            log.info(f"Loaded {short_name} ({round((end_time - start_time) * 1000, 2)} ms)")

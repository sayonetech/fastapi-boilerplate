"""Main FastAPI application."""

import time

import structlog
from fastapi import Request
from fastapi.responses import JSONResponse
from fastmcp import FastMCP

from src.beco_app import BecoApp
from src.configs import mcp_agent_config
from src.configs.logging_config import setup_logging
from src.extensions.ext_mcp import mcp_wrapper
from src.lifespan_manager import LifespanManager
from src.middleware.logging_middleware import StructuredLoggingMiddleware
from src.routes import register_routes
from src.utils import display_mcp_components

setup_logging(log_level="DEBUG" if mcp_agent_config.DEBUG else "INFO")

log = structlog.get_logger(__name__)


def create_fast_api_app_with_configs() -> BecoApp:
    """
    create a raw flask app
    with configs loaded from .env file
    """
    app_name = mcp_agent_config.APP_NAME
    app_version = mcp_agent_config.APP_VERSION
    enable_swagger = mcp_agent_config.DEPLOY_ENV == "DEVELOPMENT"
    enable_redoc = mcp_agent_config.DEPLOY_ENV == "DEVELOPMENT"
    debug = mcp_agent_config.DEBUG

    mcp = FastMCP(
        name=mcp_agent_config.MCP_APP_NAME,
        instructions=mcp_agent_config.MCP_APP_INSTRUCTION,
    )

    mcp_app = mcp.http_app(path="/")
    lifespan_manager = LifespanManager(mcp_app)

    # Add your custom startup/shutdown logic
    # Will keep the code here for reference
    async def setup_database():
        print("Setting up database...")

    async def cleanup_database():
        print("Cleaning up database...")

    async def discover_mcp_components():
        if mcp_wrapper._mcp_app is not None:
            await display_mcp_components(mcp_wrapper._mcp_app)

    async def stop_background_tasks():
        print("Stopping background tasks...")

    lifespan_manager.add_startup_task(setup_database)
    lifespan_manager.add_startup_task(discover_mcp_components)
    lifespan_manager.add_shutdown_task(stop_background_tasks)
    lifespan_manager.add_shutdown_task(cleanup_database)

    beco_app = BecoApp(
        title=app_name,
        description="A FastAPI-based MCP (Model Context Protocol) server",
        version=app_version,
        docs_url="/docs" if enable_swagger and debug else None,
        redoc_url="/redoc" if enable_redoc and debug else None,
        lifespan=lifespan_manager.lifespan,
    )

    beco_app.state.mcp_app = mcp_app
    beco_app.state.mcp = mcp

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
    """Create and configure the FastAPI application and MCP server."""
    start_time = time.perf_counter()
    app = create_fast_api_app_with_configs()

    # Add Structured Logging Middleware
    app.add_middleware(StructuredLoggingMiddleware)

    # Add global exception handler
    app.add_exception_handler(Exception, unhandled_exception_handler)

    register_routes(app)
    initialize_extensions(app)
    end_time = time.perf_counter()
    if mcp_agent_config.DEBUG:
        log.info(f"Finished create_app ({round((end_time - start_time) * 1000, 2)} ms)")
    return app


def initialize_extensions(app: BecoApp):
    from src.extensions import ext_compress, ext_cors, ext_mcp, ext_set_secretkey, ext_timezone, ext_warnings

    # TODO: Add more extensions here
    # Migrate current logging  here
    # DB will come here . In our case it is mongo db
    # Redis will come here .
    # Sentry will come here .
    # Celery will come here .
    # Import modules will come here .
    # App metrics will come here .
    extensions = [
        ext_mcp,
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
            if mcp_agent_config.DEBUG:
                log.info(f"Skipped {short_name}")
            continue

        start_time = time.perf_counter()
        ext.init_app(app)
        end_time = time.perf_counter()
        if mcp_agent_config.DEBUG:
            log.info(f"Loaded {short_name} ({round((end_time - start_time) * 1000, 2)} ms)")

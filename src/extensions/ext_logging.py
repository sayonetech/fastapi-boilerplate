import logging
import os
import sys
import uuid
from datetime import datetime
from logging.handlers import TimedRotatingFileHandler
from pathlib import Path

from fastapi import FastAPI, Request
from starlette.middleware.base import BaseHTTPMiddleware

from src.configs import madcrow_config

# --- Constants ---
LOG_FOLDER = madcrow_config.LOG_FOLDER or "logs"
LOG_DIR = Path(LOG_FOLDER)
LOG_DIR.mkdir(exist_ok=True)


# --- Request ID Middleware ---
class RequestIdMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        request.state.request_id = uuid.uuid4().hex[:10]
        response = await call_next(request)
        return response


# --- Logging Filter ---
class RequestIdFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        try:
            from starlette_context import context
            record.req_id = context.get("request_id", "")
        except Exception:
            record.req_id = ""
        return True


# --- Formatter with Request ID ---
class RequestIdFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        if not hasattr(record, "req_id"):
            record.req_id = ""
        return super().format(record)


def setup_logging(log_level: str = "INFO") -> None:
    """Setup basic logging (console + file with rotation)."""

    log_filename = LOG_DIR / f"madcrow-backend.log"

    # Timed rotating file handler (daily rotation)
    file_handler = TimedRotatingFileHandler(
        filename=log_filename,
        when="midnight",
        interval=1,
        backupCount=7,
        encoding="utf-8"
    )
    file_handler.suffix = "%Y-%m-%d"

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)

    # Formatter (human-readable, with request ID)
    formatter = RequestIdFormatter(
        fmt="%(asctime)s [%(levelname)s] [%(req_id)s] %(name)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)

    # Add request ID filter to both handlers
    file_handler.addFilter(RequestIdFilter())
    console_handler.addFilter(RequestIdFilter())

    # Setup root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level.upper())
    root_logger.handlers.clear()
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)

    logging.info("Logging initialized successfully.")


# --- Extension init hook ---
def init_app(app: FastAPI):
    """Initialize logging system and attach middleware."""
    setup_logging(log_level="DEBUG" if madcrow_config.DEBUG else "INFO")
    app.add_middleware(RequestIdMiddleware)

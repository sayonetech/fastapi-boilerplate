"""Structured logging configuration for the Madcrow backend."""

import logging
import logging.handlers
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

import structlog
from structlog.types import EventDict, WrappedLogger

from src.configs import madcrow_config  # Use your Madcrow backend config

# --- Constants ---
LOG_FOLDER = madcrow_config.LOG_FOLDER
if LOG_FOLDER is None:
    LOG_FOLDER = "logs"  # Fallback to default if None
LOG_DIR = Path(LOG_FOLDER)
LOG_DIR.mkdir(exist_ok=True)  # Ensure the log directory exists

# --- Sensitive Data Masking ---

SENSITIVE_KEYS = {"password", "token", "secret", "authorization", "access_token", "refresh_token"}


def mask_sensitive_data(logger: WrappedLogger, method_name: str, event_dict: EventDict) -> EventDict:
    """
    A structlog processor to mask sensitive keys in the log event dictionary.

    Recursively searches for keys defined in SENSITIVE_KEYS and replaces their
    values with "[REDACTED]".
    """

    def recursive_mask(data: Any) -> Any:
        if isinstance(data, dict):
            return {k: "[REDACTED]" if k.lower() in SENSITIVE_KEYS else recursive_mask(v) for k, v in data.items()}
        if isinstance(data, list):
            return [recursive_mask(item) for item in data]
        return data

    return recursive_mask(event_dict)


def setup_logging(log_level: str = "INFO") -> None:
    """
    Configure structured logging for the Madcrow backend.

    This function sets up both the standard library `logging` and `structlog`.
    - Logs are written to a daily file in the `logs` directory, named with the current date.
    - Logs are formatted as JSON for easy parsing by log management systems.
    - Sensitive data is automatically masked.
    """
    # --- Standard Library Logging Configuration ---

    # File handler with today's date in the filename
    today_str = datetime.utcnow().strftime("%Y-%m-%d")
    log_filename = LOG_DIR / f"madcrow-backend.{today_str}.log"
    file_handler = logging.FileHandler(log_filename, encoding="utf-8")
    file_handler.setFormatter(logging.Formatter("%(message)s"))  # structlog will handle the formatting

    # Console handler for development visibility
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(logging.Formatter("%(message)s"))

    # Configure the root logger
    root_logger = logging.getLogger()
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)
    root_logger.setLevel(log_level.upper())

    # --- Structlog Configuration ---
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso", utc=True),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            mask_sensitive_data,
            structlog.processors.JSONRenderer(),
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    logging.info("Logging configured successfully.")

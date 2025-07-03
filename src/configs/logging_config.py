"""Structured logging configuration for the Madcrow backend."""

import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

import structlog
from structlog.types import EventDict, WrappedLogger

from src.configs import madcrow_config

# Create logs directory if missing
LOG_FOLDER = madcrow_config.LOG_FOLDER or "logs"
LOG_DIR = Path(LOG_FOLDER)
LOG_DIR.mkdir(exist_ok=True)

# Fields to mask in logs
SENSITIVE_KEYS = {
    "password", "token", "secret", "authorization",
    "access_token", "refresh_token"
}


def mask_sensitive_data(_: WrappedLogger, __: str, event_dict: EventDict) -> EventDict:
    """Redact sensitive values recursively."""

    def recursive_mask(data: Any) -> Any:
        if isinstance(data, dict):
            return {
                k: "[REDACTED]" if k.lower() in SENSITIVE_KEYS else recursive_mask(v)
                for k, v in data.items()
            }
        if isinstance(data, list):
            return [recursive_mask(i) for i in data]
        return data

    return recursive_mask(event_dict)


def setup_logging(log_level: str = "INFO") -> None:
    """Configure standard logging and structlog."""

    today_str = datetime.utcnow().strftime("%Y-%m-%d")
    log_filename = LOG_DIR / f"madcrow-backend.{today_str}.log"

    file_handler = logging.FileHandler(log_filename, encoding="utf-8")
    file_handler.setFormatter(logging.Formatter(
        fmt="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    ))

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(logging.Formatter(
        fmt="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    ))

    root_logger = logging.getLogger()
    root_logger.setLevel(log_level.upper())
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)

    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.processors.TimeStamper(fmt="iso", utc=True),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            mask_sensitive_data,
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    logging.info("Logging configured successfully.")

import logging
import os
import sys
from logging.handlers import RotatingFileHandler
from typing import Any

from src.middleware.logging_middleware import request_id_var

from ..beco_app import BecoApp
from ..configs import madcrow_config

# Sensitive keys that should be masked in logs
SENSITIVE_KEYS = {"password", "token", "secret", "authorization", "access_token", "refresh_token"}


def mask_sensitive_data(data: Any) -> Any:
    """
    Recursively mask sensitive keys in data structures.

    Searches for keys defined in SENSITIVE_KEYS and replaces their
    values with "[REDACTED]".
    """
    if isinstance(data, dict):
        return {k: "[REDACTED]" if k.lower() in SENSITIVE_KEYS else mask_sensitive_data(v) for k, v in data.items()}
    if isinstance(data, list):
        return [mask_sensitive_data(item) for item in data]
    return data


class SensitiveDataFilter(logging.Filter):
    """Filter to mask sensitive data in log records."""

    def filter(self, record):
        # Mask sensitive data in log messages
        if hasattr(record, "msg") and isinstance(record.msg, str):
            # Simple string replacement for common sensitive patterns
            for key in SENSITIVE_KEYS:
                if key.lower() in record.msg.lower():
                    record.msg = record.msg.replace(key, f"{key}=[REDACTED]")

        # Mask sensitive data in args if they contain dicts/lists
        if hasattr(record, "args") and record.args:
            record.args = tuple(mask_sensitive_data(arg) for arg in record.args)

        return True


def init_app(app: BecoApp):
    log_handlers: list[logging.Handler] = []
    log_file = madcrow_config.get_dated_log_file()
    if log_file:
        log_dir = os.path.dirname(log_file)
        os.makedirs(log_dir, exist_ok=True)
        log_handlers.append(
            RotatingFileHandler(
                filename=log_file,
                maxBytes=madcrow_config.LOG_FILE_MAX_SIZE * 1024 * 1024,
                backupCount=madcrow_config.LOG_FILE_BACKUP_COUNT,
            )
        )

    # Always add StreamHandler to log to console
    sh = logging.StreamHandler(sys.stdout)
    log_handlers.append(sh)

    # Apply all filters to all handlers

    sensitive_filter = SensitiveDataFilter()
    request_id_filter = RequestIdFilter()

    for handler in log_handlers:
        handler.addFilter(sensitive_filter)
        handler.addFilter(request_id_filter)

    logging.basicConfig(
        level=madcrow_config.LOG_LEVEL,
        format=madcrow_config.LOG_FORMAT,
        datefmt=madcrow_config.LOG_DATEFORMAT,
        handlers=log_handlers,
        force=True,
    )

    # Apply RequestIdFormatter to all handlers
    apply_request_id_formatter()

    # Disable propagation for noisy loggers to avoid duplicate logs
    logging.getLogger("sqlalchemy.engine").propagate = False
    log_tz = madcrow_config.LOG_TZ
    if log_tz:
        from datetime import datetime

        import pytz

        timezone = pytz.timezone(log_tz)

        def time_converter(seconds):
            return datetime.fromtimestamp(seconds, tz=timezone).timetuple()

        for handler in logging.root.handlers:
            if handler.formatter:
                handler.formatter.converter = time_converter


class RequestIdFilter(logging.Filter):
    """
    Logging filter that injects the request ID into each log record.

    This filter uses a ContextVar (set by middleware) to retrieve the
    request-scoped request ID and attaches it to the log record as `req_id`,
    allowing it to be included in log format strings.

    This enables consistent request tracing in asynchronous FastAPI applications.
    """

    def filter(self, record):
        record.req_id = request_id_var.get("")  # from your middleware
        return True


class RequestIdFormatter(logging.Formatter):
    def format(self, record):
        if not hasattr(record, "req_id"):
            record.req_id = ""
        return super().format(record)


def apply_request_id_formatter():
    for handler in logging.root.handlers:
        if handler.formatter:
            handler.formatter = RequestIdFormatter(madcrow_config.LOG_FORMAT, madcrow_config.LOG_DATEFORMAT)

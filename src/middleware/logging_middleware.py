"""Middleware for structured request and response logging."""

import logging
import time
import uuid
from contextvars import ContextVar

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint

# Context variables for request-specific data
trace_id_var: ContextVar[str] = ContextVar("trace_id", default="")
request_id_var: ContextVar[str] = ContextVar("request_id", default="")

log = logging.getLogger(__name__)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    FastAPI middleware to log HTTP requests and responses with trace ID tracking.

    This middleware captures key information about each HTTP request and its
    corresponding response, including a unique trace ID, timing, status code,
    and client information. Uses standard Python logging with context variables
    for request-scoped data.
    """

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        """
        Process and log a single request/response cycle.
        """
        # --- Pre-Request ---
        start_time = time.monotonic()
        self.bind_context(request)

        # --- Process Request ---
        response = await call_next(request)

        # --- Post-Request ---
        duration_ms = (time.monotonic() - start_time) * 1000

        client_ip = request.client.host if request.client else "unknown"
        trace_id = trace_id_var.get()
        log.info(
            f"Request completed - {request.method} {request.url.path} - "
            f"Status: {response.status_code} - Duration: {round(duration_ms, 2)}ms - "
            f"Client: {client_ip} - Trace ID: {trace_id}"
        )

        return response

    def bind_context(self, request: Request) -> None:
        """
        Bind request-specific context to the logger.

        This includes a unique trace ID for correlating logs for a single request.
        """
        trace_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        trace_id_var.set(trace_id)
        request_id_var.set(trace_id)

"""Middleware for structured request and response logging."""

import time
import uuid

import structlog
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint

log = structlog.get_logger(__name__)


class StructuredLoggingMiddleware(BaseHTTPMiddleware):
    """
    FastAPI middleware to log requests and responses in a structured format.

    This middleware captures key information about each HTTP request and its
    corresponding response, including a unique trace ID, timing, and status.
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

        log.info(
            "Request completed",
            http={
                "request": {
                    "method": request.method,
                    "path": request.url.path,
                    "query": str(request.url.query),
                },
                "response": {
                    "status_code": response.status_code,
                },
                "duration_ms": round(duration_ms, 2),
            },
            network={
                "client": {
                    "ip": request.client.host if request.client else "unknown",
                    "user_agent": request.headers.get("user-agent", "unknown"),
                }
            },
        )

        return response

    def bind_context(self, request: Request) -> None:
        """
        Bind request-specific context to the logger.

        This includes a unique trace ID for correlating logs for a single request.
        """
        trace_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        structlog.contextvars.clear_contextvars()
        structlog.contextvars.bind_contextvars(
            trace_id=trace_id,
            request_id=trace_id,  # often used as an alias
            http={
                "request": {
                    "method": request.method,
                    "path": request.url.path,
                }
            },
            network={"client": {"ip": request.client.host if request.client else "unknown"}},
        )

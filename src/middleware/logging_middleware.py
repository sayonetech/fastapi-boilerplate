"""Middleware for structured request and response logging."""

import time
import uuid
import logging
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint

log = logging.getLogger(__name__)  


class StructuredLoggingMiddleware(BaseHTTPMiddleware):
    """
    FastAPI middleware to log requests and responses in a structured format.

    This middleware captures key information about each HTTP request and its
    corresponding response, including a unique trace ID, timing, and status.
    """

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        # --- Pre-Request ---
        start_time = time.monotonic()
        trace_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))

        # --- Process Request ---
        response = await call_next(request)

        # --- Post-Request ---
        duration_ms = (time.monotonic() - start_time) * 1000

        log.info(
            "Request completed",
            extra={
                "trace_id": trace_id,
                "method": request.method,
                "path": request.url.path,
                "query": request.url.query,
                "status_code": response.status_code,
                "duration_ms": round(duration_ms, 2),
                "client_ip": request.client.host if request.client else "unknown",
                "user_agent": request.headers.get("user-agent", "unknown"),
            }
        )

        return response

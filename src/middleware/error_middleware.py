"""Enhanced error handling middleware for FastAPI."""

import logging
import time

from fastapi import Request, Response
from fastapi.responses import JSONResponse
from pydantic import ValidationError as PydanticValidationError
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint

from ..configs import madcrow_config
from ..exceptions import MadcrowHTTPError
from ..utils.error_factory import ErrorResponseFactory

logger = logging.getLogger(__name__)


class ErrorHandlingMiddleware(BaseHTTPMiddleware):
    """
    Enhanced error handling middleware that provides consistent error responses.

    This middleware catches all exceptions and converts them to standardized
    JSON error responses with proper logging and error tracking.
    """

    def __init__(self, app, include_debug_info: bool = False):
        """
        Initialize the error handling middleware.

        Args:
            app: FastAPI application instance
            include_debug_info: Whether to include debug information in error responses
        """
        super().__init__(app)
        self.include_debug_info = include_debug_info or madcrow_config.DEBUG

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        """
        Process request and handle any exceptions that occur.

        Args:
            request: The incoming HTTP request
            call_next: The next middleware or route handler

        Returns:
            HTTP response, either successful or error response
        """
        start_time = time.monotonic()

        try:
            # Process the request
            response = await call_next(request)
            return response

        except Exception as exc:
            # Calculate request duration for logging
            duration_ms = (time.monotonic() - start_time) * 1000

            # Log the exception with context
            self._log_exception(exc, request, duration_ms)

            # Create standardized error response
            error_response = ErrorResponseFactory.from_exception(
                exception=exc,
                request=request,
                include_debug_info=self.include_debug_info,
            )

            # Determine HTTP status code
            status_code = self._get_status_code(exc)

            # Create JSON response
            return JSONResponse(
                status_code=status_code,
                content=error_response,
                headers=self._get_error_headers(exc),
            )

    def _log_exception(self, exc: Exception, request: Request, duration_ms: float) -> None:
        """
        Log exception with appropriate level and context.

        Args:
            exc: The exception that occurred
            request: The HTTP request
            duration_ms: Request duration in milliseconds
        """
        # Prepare log context
        log_context = {
            "method": request.method,
            "path": str(request.url.path),
            "duration_ms": round(duration_ms, 2),
            "client_ip": request.client.host if request.client else "unknown",
            "user_agent": request.headers.get("user-agent", "unknown"),
        }

        # Add query parameters if present
        if request.url.query:
            log_context["query_params"] = str(request.url.query)

        # Determine log level based on exception type
        if isinstance(exc, MadcrowHTTPError):
            if exc.status_code >= 500:
                logger.error(
                    f"Server error: {exc.message}",
                    extra={"error_id": exc.error_id, **log_context},
                    exc_info=exc.cause if exc.cause else None,
                )
            elif exc.status_code >= 400:
                logger.warning(
                    f"Client error: {exc.message}",
                    extra={"error_id": exc.error_id, **log_context},
                )
            else:
                logger.info(
                    f"Request error: {exc.message}",
                    extra={"error_id": exc.error_id, **log_context},
                )
        elif isinstance(exc, PydanticValidationError):
            logger.warning(
                f"Validation error: {len(exc.errors())} validation failures",
                extra=log_context,
            )
        else:
            # Unexpected exceptions are always logged as errors
            logger.exception(
                f"Unexpected exception: {type(exc).__name__}: {str(exc)}",
                extra=log_context,
                exc_info=exc,
            )

    def _get_status_code(self, exc: Exception) -> int:
        """
        Determine the appropriate HTTP status code for an exception.

        Args:
            exc: The exception

        Returns:
            HTTP status code
        """
        if isinstance(exc, MadcrowHTTPError):
            return exc.status_code
        elif isinstance(exc, PydanticValidationError):
            return 422  # Unprocessable Entity
        else:
            return 500  # Internal Server Error

    def _get_error_headers(self, exc: Exception) -> dict:
        """
        Get additional headers to include in error response.

        Args:
            exc: The exception

        Returns:
            Dictionary of headers
        """
        headers = {"Content-Type": "application/json"}

        # Add exception-specific headers
        if isinstance(exc, MadcrowHTTPError) and exc.headers:
            headers.update(exc.headers)

        # Add CORS headers if needed (this should be handled by CORS middleware)
        # but we can add security headers here if needed

        return headers


def create_error_handlers() -> dict:
    """
    Create FastAPI exception handlers for specific exception types.

    Returns:
        Dictionary mapping exception types to handler functions
    """

    async def madcrow_http_error_handler(request: Request, exc: MadcrowHTTPError) -> JSONResponse:
        """Handle MadcrowHTTPError exceptions."""
        error_response = ErrorResponseFactory.from_exception(
            exception=exc,
            request=request,
            include_debug_info=madcrow_config.DEBUG,
        )

        return JSONResponse(
            status_code=exc.status_code,
            content=error_response,
            headers=exc.headers,
        )

    async def validation_error_handler(request: Request, exc: PydanticValidationError) -> JSONResponse:
        """Handle Pydantic validation errors."""
        error_response = ErrorResponseFactory.from_exception(
            exception=exc,
            request=request,
            include_debug_info=madcrow_config.DEBUG,
        )

        return JSONResponse(
            status_code=422,
            content=error_response,
        )

    async def generic_error_handler(request: Request, exc: Exception) -> JSONResponse:
        """Handle all other exceptions."""
        logger.exception("Unhandled exception", exc_info=exc)

        error_response = ErrorResponseFactory.from_exception(
            exception=exc,
            request=request,
            include_debug_info=madcrow_config.DEBUG,
        )

        return JSONResponse(
            status_code=500,
            content=error_response,
        )

    return {
        MadcrowHTTPError: madcrow_http_error_handler,
        PydanticValidationError: validation_error_handler,
        Exception: generic_error_handler,
    }

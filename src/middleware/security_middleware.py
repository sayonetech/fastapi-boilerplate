"""Security headers middleware for FastAPI applications."""

import logging

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint

from ..configs import madcrow_config

log = logging.getLogger(__name__)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    FastAPI middleware to add comprehensive security headers to HTTP responses.

    This middleware adds various security headers to protect against common
    web vulnerabilities including XSS, clickjacking, MIME sniffing, and more.

    Security headers included:
    - HTTP Strict Transport Security (HSTS)
    - Content Security Policy (CSP)
    - X-Frame-Options
    - X-Content-Type-Options
    - X-XSS-Protection
    - Referrer-Policy
    - Permissions-Policy
    - Server header modification
    """

    def __init__(self, app, **kwargs):
        super().__init__(app, **kwargs)
        self._security_headers = self._build_security_headers()
        log.info("Security headers middleware initialized")

    def _build_security_headers(self) -> dict[str, str]:
        """Build the security headers dictionary based on configuration."""
        headers = {}

        # HSTS (HTTP Strict Transport Security)
        if madcrow_config.SECURITY_HSTS_ENABLED:
            hsts_value = f"max-age={madcrow_config.SECURITY_HSTS_MAX_AGE}"
            if madcrow_config.SECURITY_HSTS_INCLUDE_SUBDOMAINS:
                hsts_value += "; includeSubDomains"
            if madcrow_config.SECURITY_HSTS_PRELOAD:
                hsts_value += "; preload"
            headers["Strict-Transport-Security"] = hsts_value

        # Content Security Policy
        if madcrow_config.SECURITY_CSP_ENABLED:
            csp_directives = [
                f"default-src {madcrow_config.SECURITY_CSP_DEFAULT_SRC}",
                f"script-src {madcrow_config.SECURITY_CSP_SCRIPT_SRC}",
                f"style-src {madcrow_config.SECURITY_CSP_STYLE_SRC}",
                f"img-src {madcrow_config.SECURITY_CSP_IMG_SRC}",
                f"font-src {madcrow_config.SECURITY_CSP_FONT_SRC}",
                f"connect-src {madcrow_config.SECURITY_CSP_CONNECT_SRC}",
                f"frame-ancestors {madcrow_config.SECURITY_CSP_FRAME_ANCESTORS}",
            ]
            headers["Content-Security-Policy"] = "; ".join(csp_directives)
            log.debug("CSP enabled with configured directives")

        # X-Frame-Options
        headers["X-Frame-Options"] = madcrow_config.SECURITY_X_FRAME_OPTIONS

        # X-Content-Type-Options
        if madcrow_config.SECURITY_X_CONTENT_TYPE_OPTIONS:
            headers["X-Content-Type-Options"] = "nosniff"

        # X-XSS-Protection
        if madcrow_config.SECURITY_X_XSS_PROTECTION:
            headers["X-XSS-Protection"] = "1; mode=block"

        # Referrer Policy
        headers["Referrer-Policy"] = madcrow_config.SECURITY_REFERRER_POLICY

        # Permissions Policy
        if madcrow_config.SECURITY_PERMISSIONS_POLICY_ENABLED:
            headers["Permissions-Policy"] = madcrow_config.SECURITY_PERMISSIONS_POLICY

        return headers

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        """
        Process request and add security headers to response.

        Documentation endpoints (/docs, /redoc, etc.) are excluded from security headers
        to ensure they work properly without CSP restrictions.
        """
        # Process the request
        response = await call_next(request)

        # Skip security headers entirely for documentation endpoints
        if self._is_documentation_endpoint(request.url.path):
            log.debug(f"Skipping security headers for documentation endpoint: {request.url.path}")
            return response

        # Add security headers to all non-documentation responses
        for header_name, header_value in self._security_headers.items():
            response.headers[header_name] = header_value

        # Handle Server header
        if "server" in response.headers:
            del response.headers["server"]  # Always remove default server header

        # Either hide completely or set custom value (mutually exclusive)
        if madcrow_config.SECURITY_HIDE_SERVER_HEADER:
            # Keep server header completely hidden
            pass
        elif madcrow_config.SECURITY_SERVER_HEADER_VALUE:
            # Set custom server header only if not hidden
            response.headers["Server"] = madcrow_config.SECURITY_SERVER_HEADER_VALUE

        # Add security-specific headers for development/debugging
        if madcrow_config.DEBUG:
            response.headers["X-Security-Headers"] = "enabled"

        return response

    def get_configured_headers(self) -> dict[str, str]:
        """Get the currently configured security headers (for debugging/testing)."""
        return self._security_headers.copy()

    def _is_documentation_endpoint(self, path: str) -> bool:
        """Check if the request path is for Swagger UI or ReDoc documentation."""
        docs_paths = ["/docs", "/redoc", "/openapi.json", "/docs/oauth2-redirect"]
        return any(path.startswith(doc_path) for doc_path in docs_paths)


class SecurityHeadersConfig:
    """
    Configuration helper for security headers.

    Provides methods to validate and get security header configurations.
    """

    @staticmethod
    def validate_csp_directive(directive: str) -> bool:
        """Validate a CSP directive format."""
        if not directive or not directive.strip():
            return False

        # Basic validation - check for common CSP keywords
        valid_keywords = {"'self'", "'none'", "'unsafe-inline'", "'unsafe-eval'", "'strict-dynamic'", "'unsafe-hashes'"}

        parts = directive.split()
        for part in parts:
            if (
                part.startswith("'")
                and part.endswith("'")
                and part not in valid_keywords
                and not part.startswith("'nonce-")
                and not part.startswith("'sha")
            ):
                return False

        return True

    @staticmethod
    def get_development_csp() -> str:
        """Get a more permissive CSP for development environments."""
        return (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: https:; "
            "font-src 'self' data:; "
            "connect-src 'self' ws: wss:; "
            "frame-ancestors 'none'"
        )

    @staticmethod
    def get_production_csp() -> str:
        """Get a strict CSP for production environments."""
        return (
            "default-src 'self'; "
            "script-src 'self'; "
            "style-src 'self'; "
            "img-src 'self' data: https:; "
            "font-src 'self'; "
            "connect-src 'self'; "
            "frame-ancestors 'none'; "
            "base-uri 'self'; "
            "form-action 'self'"
        )

    @classmethod
    def get_recommended_headers_for_environment(cls, is_production: bool = False) -> dict[str, str]:
        """Get recommended security headers based on environment."""
        base_headers = {
            "X-Frame-Options": "DENY",
            "X-Content-Type-Options": "nosniff",
            "X-XSS-Protection": "1; mode=block",
            "Referrer-Policy": "strict-origin-when-cross-origin",
            "Permissions-Policy": "geolocation=(), microphone=(), camera=(), payment=(), usb=()",
        }

        if is_production:
            base_headers.update(
                {
                    "Strict-Transport-Security": "max-age=31536000; includeSubDomains; preload",
                    "Content-Security-Policy": cls.get_production_csp(),
                }
            )
        else:
            base_headers.update(
                {
                    "Content-Security-Policy": cls.get_development_csp(),
                }
            )

        return base_headers

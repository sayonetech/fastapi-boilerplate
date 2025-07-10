"""Security extension for FastAPI application."""

import logging

from ..beco_app import BecoApp
from ..configs import madcrow_config
from ..middleware.security_middleware import SecurityHeadersMiddleware

log = logging.getLogger(__name__)


def is_enabled() -> bool:
    """Check if security headers middleware should be enabled."""
    return madcrow_config.SECURITY_HEADERS_ENABLED


def init_app(app: BecoApp) -> None:
    """Initialize security middleware with proper configuration."""
    try:
        log.info("Initializing security headers middleware...")

        # Validate configuration
        _validate_security_config()

        # Add security headers middleware
        app.add_middleware(SecurityHeadersMiddleware)

        # Log security configuration in debug mode
        if madcrow_config.DEBUG:
            _log_security_config()

        log.info("Security headers middleware initialized successfully")

    except Exception:
        log.exception("Failed to initialize security middleware")
        raise


def _validate_security_config() -> None:
    """Validate security configuration settings."""
    errors = []

    # Validate HSTS max-age
    if madcrow_config.SECURITY_HSTS_ENABLED:
        if madcrow_config.SECURITY_HSTS_MAX_AGE < 0:
            errors.append("SECURITY_HSTS_MAX_AGE must be non-negative")
        elif madcrow_config.SECURITY_HSTS_MAX_AGE < 300:  # 5 minutes minimum
            log.warning("SECURITY_HSTS_MAX_AGE is less than 5 minutes, consider increasing for better security")

    # Validate X-Frame-Options
    valid_frame_options = {"DENY", "SAMEORIGIN"}
    if (
        madcrow_config.SECURITY_X_FRAME_OPTIONS not in valid_frame_options
        and not madcrow_config.SECURITY_X_FRAME_OPTIONS.startswith("ALLOW-FROM ")
    ):
        errors.append(f"SECURITY_X_FRAME_OPTIONS must be one of {valid_frame_options} or start with 'ALLOW-FROM '")

    # Validate Referrer Policy
    valid_referrer_policies = {
        "no-referrer",
        "no-referrer-when-downgrade",
        "origin",
        "origin-when-cross-origin",
        "same-origin",
        "strict-origin",
        "strict-origin-when-cross-origin",
        "unsafe-url",
    }
    if madcrow_config.SECURITY_REFERRER_POLICY not in valid_referrer_policies:
        errors.append(f"SECURITY_REFERRER_POLICY must be one of {valid_referrer_policies}")

    # Validate CSP directives (basic validation)
    if madcrow_config.SECURITY_CSP_ENABLED:
        csp_directives = [
            ("SECURITY_CSP_DEFAULT_SRC", madcrow_config.SECURITY_CSP_DEFAULT_SRC),
            ("SECURITY_CSP_SCRIPT_SRC", madcrow_config.SECURITY_CSP_SCRIPT_SRC),
            ("SECURITY_CSP_STYLE_SRC", madcrow_config.SECURITY_CSP_STYLE_SRC),
            ("SECURITY_CSP_IMG_SRC", madcrow_config.SECURITY_CSP_IMG_SRC),
            ("SECURITY_CSP_FONT_SRC", madcrow_config.SECURITY_CSP_FONT_SRC),
            ("SECURITY_CSP_CONNECT_SRC", madcrow_config.SECURITY_CSP_CONNECT_SRC),
            ("SECURITY_CSP_FRAME_ANCESTORS", madcrow_config.SECURITY_CSP_FRAME_ANCESTORS),
        ]

        for directive_name, directive_value in csp_directives:
            if not directive_value or not directive_value.strip():
                errors.append(f"{directive_name} cannot be empty when CSP is enabled")

    if errors:
        error_message = "Security configuration validation failed:\n" + "\n".join(f"- {error}" for error in errors)
        raise ValueError(error_message)


def _log_security_config() -> None:
    """Log current security configuration for debugging."""
    log.debug("Security Headers Configuration:")
    log.debug(f"  HSTS Enabled: {madcrow_config.SECURITY_HSTS_ENABLED}")
    if madcrow_config.SECURITY_HSTS_ENABLED:
        log.debug(f"    Max-Age: {madcrow_config.SECURITY_HSTS_MAX_AGE}")
        log.debug(f"    Include Subdomains: {madcrow_config.SECURITY_HSTS_INCLUDE_SUBDOMAINS}")
        log.debug(f"    Preload: {madcrow_config.SECURITY_HSTS_PRELOAD}")

    log.debug(f"  CSP Enabled: {madcrow_config.SECURITY_CSP_ENABLED}")
    if madcrow_config.SECURITY_CSP_ENABLED:
        log.debug(f"    Default-src: {madcrow_config.SECURITY_CSP_DEFAULT_SRC}")
        log.debug(f"    Script-src: {madcrow_config.SECURITY_CSP_SCRIPT_SRC}")
        log.debug(f"    Style-src: {madcrow_config.SECURITY_CSP_STYLE_SRC}")

    log.debug(f"  X-Frame-Options: {madcrow_config.SECURITY_X_FRAME_OPTIONS}")
    log.debug(f"  X-Content-Type-Options: {madcrow_config.SECURITY_X_CONTENT_TYPE_OPTIONS}")
    log.debug(f"  X-XSS-Protection: {madcrow_config.SECURITY_X_XSS_PROTECTION}")
    log.debug(f"  Referrer-Policy: {madcrow_config.SECURITY_REFERRER_POLICY}")
    log.debug(f"  Permissions-Policy Enabled: {madcrow_config.SECURITY_PERMISSIONS_POLICY_ENABLED}")
    log.debug(f"  Hide Server Header: {madcrow_config.SECURITY_HIDE_SERVER_HEADER}")


def get_security_info() -> dict:
    """Get current security configuration info (for health checks or debugging)."""
    return {
        "security_headers_enabled": madcrow_config.SECURITY_HEADERS_ENABLED,
        "hsts_enabled": madcrow_config.SECURITY_HSTS_ENABLED,
        "csp_enabled": madcrow_config.SECURITY_CSP_ENABLED,
        "x_frame_options": madcrow_config.SECURITY_X_FRAME_OPTIONS,
        "referrer_policy": madcrow_config.SECURITY_REFERRER_POLICY,
        "server_header_hidden": madcrow_config.SECURITY_HIDE_SERVER_HEADER,
    }

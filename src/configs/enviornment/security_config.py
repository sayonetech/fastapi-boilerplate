from pydantic import Field
from pydantic_settings import BaseSettings


class SecurityConfig(BaseSettings):
    """
    Security-related configurations for the application
    """

    def model_post_init(self, __context) -> None:
        """Validate security configuration after initialization."""
        # Warn about emergency lockdown mode
        if self.RATE_LIMIT_LOGIN_MAX_ATTEMPTS == 0 and self.RATE_LIMIT_LOGIN_ENABLED:
            import logging

            logger = logging.getLogger(__name__)
            logger.warning(
                "EMERGENCY LOCKDOWN MODE: RATE_LIMIT_LOGIN_MAX_ATTEMPTS=0 will block ALL login attempts. "
                "Set RATE_LIMIT_LOGIN_ENABLED=false to disable rate limiting entirely."
            )

    SECRET_KEY: str = Field(
        description="Secret key for secure session cookie signing."
        "Make sure you are changing this key for your deployment with a strong key."
        "Generate a strong key using `openssl rand -base64 42` or set via the `SECRET_KEY` environment variable.",
        default="",
    )

    # Authentication Configuration
    LOGIN_DISABLED: bool = Field(
        description="Disable login requirements for testing purposes. WARNING: Only use in development/testing!",
        default=False,
    )

    # Rate Limiting Configuration
    RATE_LIMIT_LOGIN_ENABLED: bool = Field(
        description="Enable rate limiting for login attempts",
        default=True,
    )
    RATE_LIMIT_LOGIN_MAX_ATTEMPTS: int = Field(
        description="Maximum number of failed login attempts before rate limiting. "
        "Set to 0 for emergency lockdown mode (blocks ALL login attempts). "
        "Use RATE_LIMIT_LOGIN_ENABLED=false to disable rate limiting entirely.",
        default=5,
        ge=0,
        le=100,
    )
    RATE_LIMIT_LOGIN_TIME_WINDOW: int = Field(
        description="Time window in seconds for login rate limiting",
        default=900,  # 15 minutes
        ge=60,
        le=86400,  # 24 hours
    )

    # Security Headers Configuration
    SECURITY_HEADERS_ENABLED: bool = Field(
        description="Enable or disable security headers middleware",
        default=True,
    )

    # HSTS (HTTP Strict Transport Security)
    SECURITY_HSTS_ENABLED: bool = Field(
        description="Enable HTTP Strict Transport Security header",
        default=True,
    )
    SECURITY_HSTS_MAX_AGE: int = Field(
        description="HSTS max-age directive in seconds (default: 1 year)",
        default=31536000,  # 1 year
    )
    SECURITY_HSTS_INCLUDE_SUBDOMAINS: bool = Field(
        description="Include subdomains in HSTS policy",
        default=True,
    )
    SECURITY_HSTS_PRELOAD: bool = Field(
        description="Enable HSTS preload directive",
        default=False,
    )

    # Content Security Policy
    SECURITY_CSP_ENABLED: bool = Field(
        description="Enable Content Security Policy header",
        default=True,
    )
    SECURITY_CSP_DEFAULT_SRC: str = Field(
        description="CSP default-src directive",
        default="'self'",
    )
    SECURITY_CSP_SCRIPT_SRC: str = Field(
        description="CSP script-src directive",
        default="'self' 'unsafe-inline'",
    )
    SECURITY_CSP_STYLE_SRC: str = Field(
        description="CSP style-src directive",
        default="'self' 'unsafe-inline'",
    )
    SECURITY_CSP_IMG_SRC: str = Field(
        description="CSP img-src directive",
        default="'self' data: https:",
    )
    SECURITY_CSP_FONT_SRC: str = Field(
        description="CSP font-src directive",
        default="'self'",
    )
    SECURITY_CSP_CONNECT_SRC: str = Field(
        description="CSP connect-src directive",
        default="'self'",
    )
    SECURITY_CSP_FRAME_ANCESTORS: str = Field(
        description="CSP frame-ancestors directive",
        default="'none'",
    )

    # X-Frame-Options
    SECURITY_X_FRAME_OPTIONS: str = Field(
        description="X-Frame-Options header value",
        default="DENY",
    )

    # X-Content-Type-Options
    SECURITY_X_CONTENT_TYPE_OPTIONS: bool = Field(
        description="Enable X-Content-Type-Options: nosniff header",
        default=True,
    )

    # X-XSS-Protection
    SECURITY_X_XSS_PROTECTION: bool = Field(
        description="Enable X-XSS-Protection header",
        default=True,
    )

    # Referrer Policy
    SECURITY_REFERRER_POLICY: str = Field(
        description="Referrer-Policy header value",
        default="strict-origin-when-cross-origin",
    )

    # Permissions Policy
    SECURITY_PERMISSIONS_POLICY_ENABLED: bool = Field(
        description="Enable Permissions-Policy header",
        default=True,
    )
    SECURITY_PERMISSIONS_POLICY: str = Field(
        description="Permissions-Policy header value",
        default=(
            "geolocation=(), microphone=(), camera=(), payment=(), usb=(), magnetometer=(), gyroscope=(), speaker=()"
        ),
    )

    # Server Header
    SECURITY_HIDE_SERVER_HEADER: bool = Field(
        description="Completely hide the Server header (takes precedence over SECURITY_SERVER_HEADER_VALUE)",
        default=True,
    )
    SECURITY_SERVER_HEADER_VALUE: str = Field(
        description="Custom Server header value (only used when SECURITY_HIDE_SERVER_HEADER=False)",
        default="Madcrow-API",
    )

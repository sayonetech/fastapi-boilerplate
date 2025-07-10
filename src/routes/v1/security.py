"""Security information and testing routes."""

from fastapi import HTTPException
from pydantic import BaseModel

from ...configs import madcrow_config
from ...extensions.ext_security import get_security_info
from ..base_router import BaseRouter
from ..cbv import cbv, get

security_router = BaseRouter(prefix="/v1/security", tags=["security"])


class SecurityInfoResponse(BaseModel):
    """Response model for security information."""

    security_enabled: bool
    headers_configured: dict
    environment: str
    debug_mode: bool
    recommendations: list[str] = []


class SecurityHeadersResponse(BaseModel):
    """Response model for security headers test."""

    message: str
    headers_applied: dict
    configuration: dict


@cbv(security_router)
class SecurityController:
    """Security information and testing controller."""

    @get("/info", response_model=SecurityInfoResponse, operation_id="get_security_info")
    async def get_security_info(self) -> SecurityInfoResponse:
        """Get current security configuration information."""
        try:
            security_info = get_security_info()
            recommendations = []

            # Generate recommendations based on current config
            if madcrow_config.DEPLOY_ENV == "PRODUCTION":
                if not madcrow_config.SECURITY_HSTS_ENABLED:
                    recommendations.append("Enable HSTS for production environment")
                if madcrow_config.SECURITY_CSP_SCRIPT_SRC == "'self' 'unsafe-inline'":
                    recommendations.append("Consider removing 'unsafe-inline' from CSP script-src in production")
                if madcrow_config.SECURITY_HSTS_MAX_AGE < 31536000:  # 1 year
                    recommendations.append("Consider increasing HSTS max-age to at least 1 year for production")

            if not madcrow_config.SECURITY_HSTS_PRELOAD and madcrow_config.DEPLOY_ENV == "PRODUCTION":
                recommendations.append("Consider enabling HSTS preload for maximum security")

            return SecurityInfoResponse(
                security_enabled=madcrow_config.SECURITY_HEADERS_ENABLED,
                headers_configured=security_info,
                environment=madcrow_config.DEPLOY_ENV,
                debug_mode=madcrow_config.DEBUG,
                recommendations=recommendations,
            )
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to get security info: {str(e)}",
            ) from e

    @get("/headers", response_model=SecurityHeadersResponse, operation_id="test_security_headers")
    async def test_security_headers(self) -> SecurityHeadersResponse:
        """Test endpoint to verify security headers are applied."""
        try:
            # This endpoint will have security headers applied by the middleware
            # The response will show what headers are configured

            from ...middleware.security_middleware import SecurityHeadersMiddleware

            # Create a temporary instance to get configured headers
            temp_middleware = SecurityHeadersMiddleware(None)
            configured_headers = temp_middleware.get_configured_headers()

            configuration = {
                "hsts_enabled": madcrow_config.SECURITY_HSTS_ENABLED,
                "csp_enabled": madcrow_config.SECURITY_CSP_ENABLED,
                "x_frame_options": madcrow_config.SECURITY_X_FRAME_OPTIONS,
                "referrer_policy": madcrow_config.SECURITY_REFERRER_POLICY,
                "server_header_hidden": madcrow_config.SECURITY_HIDE_SERVER_HEADER,
            }

            return SecurityHeadersResponse(
                message="Security headers are configured and should be applied to this response",
                headers_applied=configured_headers,
                configuration=configuration,
            )
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to test security headers: {str(e)}",
            ) from e

    @get("/csp-report", operation_id="csp_report_endpoint")
    async def csp_report_endpoint(self) -> dict:
        """
        Endpoint for CSP violation reports.

        Note: This is a placeholder. In production, you would:
        1. Accept POST requests with CSP violation reports
        2. Log the violations for analysis
        3. Potentially alert on repeated violations
        """
        if madcrow_config.DEBUG:
            return {
                "message": "CSP report endpoint (placeholder)",
                "note": "In production, this would accept POST requests with CSP violation reports",
                "csp_enabled": madcrow_config.SECURITY_CSP_ENABLED,
            }
        else:
            raise HTTPException(status_code=404, detail="Not found")

    @get("/recommendations", operation_id="get_security_recommendations")
    async def get_security_recommendations(self) -> dict:
        """Get security recommendations based on current configuration and environment."""
        try:
            recommendations = {
                "general": [
                    "Regularly update dependencies to patch security vulnerabilities",
                    "Use HTTPS in production with valid SSL certificates",
                    "Implement proper authentication and authorization",
                    "Enable request rate limiting",
                    "Monitor and log security events",
                ],
                "headers": [],
                "environment_specific": [],
            }

            # Header-specific recommendations
            if not madcrow_config.SECURITY_HEADERS_ENABLED:
                recommendations["headers"].append("Enable security headers middleware")

            if madcrow_config.SECURITY_CSP_ENABLED:
                if "'unsafe-inline'" in madcrow_config.SECURITY_CSP_SCRIPT_SRC:
                    recommendations["headers"].append(
                        "Consider removing 'unsafe-inline' from CSP script-src and use nonces or hashes"
                    )
                if "'unsafe-eval'" in madcrow_config.SECURITY_CSP_SCRIPT_SRC:
                    recommendations["headers"].append("Avoid 'unsafe-eval' in CSP script-src")

            # Environment-specific recommendations
            if madcrow_config.DEPLOY_ENV == "PRODUCTION":
                recommendations["environment_specific"].extend(
                    [
                        "Ensure HSTS is enabled with appropriate max-age",
                        "Use strict CSP policies",
                        "Hide server information",
                        "Enable HSTS preload if possible",
                        "Regularly test security headers with online tools",
                    ]
                )
            else:
                recommendations["environment_specific"].extend(
                    [
                        "Test security headers in development environment",
                        "Prepare stricter CSP policies for production",
                        "Validate security configuration before deployment",
                    ]
                )

            return {
                "environment": madcrow_config.DEPLOY_ENV,
                "recommendations": recommendations,
                "security_tools": [
                    "https://securityheaders.com/ - Test your security headers",
                    "https://observatory.mozilla.org/ - Mozilla Observatory",
                    "https://csp-evaluator.withgoogle.com/ - CSP Evaluator",
                ],
            }
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to get security recommendations: {str(e)}",
            ) from e

"""Test script to verify security headers are working correctly."""

import asyncio
import logging

import httpx

# Configure logging
logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)


async def test_security_headers():
    """Test that security headers are properly applied to responses."""
    base_url = "http://localhost:5001"

    # Expected security headers
    expected_headers = {
        "strict-transport-security": "max-age=31536000; includeSubDomains",
        "content-security-policy": (
            "default-src 'self'; script-src 'self' 'unsafe-inline'; "
            "style-src 'self' 'unsafe-inline'; img-src 'self' data: https:; "
            "font-src 'self'; connect-src 'self'; frame-ancestors 'none'"
        ),
        "x-frame-options": "DENY",
        "x-content-type-options": "nosniff",
        "x-xss-protection": "1; mode=block",
        "referrer-policy": "strict-origin-when-cross-origin",
        "permissions-policy": (
            "geolocation=(), microphone=(), camera=(), payment=(), usb=(), magnetometer=(), gyroscope=(), speaker=()"
        ),
    }

    endpoints_to_test = [
        "/api/v1/health",
        "/api/v1/health/ready",
        "/api/v1/health/live",
    ]

    async with httpx.AsyncClient() as client:
        for endpoint in endpoints_to_test:
            try:
                log.info(f"Testing endpoint: {endpoint}")
                response = await client.get(f"{base_url}{endpoint}")

                log.info(f"Status Code: {response.status_code}")

                # Check for expected security headers
                missing_headers = []
                present_headers = []

                for header_name, expected_value in expected_headers.items():
                    actual_value = response.headers.get(header_name.lower())
                    if actual_value:
                        present_headers.append(f"✅ {header_name}: {actual_value}")
                        # For some headers, we just check presence, not exact value
                        if header_name in ["content-security-policy", "permissions-policy"]:
                            if expected_value.split(";")[0].strip() not in actual_value:
                                log.warning(f"⚠️  {header_name} value differs from expected")
                    else:
                        missing_headers.append(f"❌ {header_name}: MISSING")

                # Check for server header (should be custom or completely hidden)
                server_header = response.headers.get("server")
                if server_header:
                    present_headers.append(f"✅ server: {server_header}")
                else:
                    present_headers.append("✅ server: HIDDEN (as configured)")

                # Check for debug header in development
                debug_header = response.headers.get("x-security-headers")
                if debug_header:
                    present_headers.append(f"✅ x-security-headers: {debug_header}")

                # Print results
                log.info("Security Headers Status:")
                for header in present_headers:
                    log.info(f"  {header}")

                if missing_headers:
                    log.error("Missing Security Headers:")
                    for header in missing_headers:
                        log.error(f"  {header}")
                else:
                    log.info("✅ All expected security headers are present!")

                log.info("-" * 60)

            except Exception as e:
                log.exception(f"Error testing endpoint {endpoint}")


def print_security_headers_info():
    """Print information about the security headers implementation."""
    print("\n" + "=" * 80)
    print("SECURITY HEADERS MIDDLEWARE - IMPLEMENTATION SUMMARY")
    print("=" * 80)

    print("\n🔒 SECURITY HEADERS IMPLEMENTED:")
    print("  • HTTP Strict Transport Security (HSTS)")
    print("    - Enforces HTTPS connections")
    print("    - Configurable max-age, includeSubDomains, preload")
    print()
    print("  • Content Security Policy (CSP)")
    print("    - Prevents XSS attacks")
    print("    - Configurable directives for scripts, styles, images, etc.")
    print()
    print("  • X-Frame-Options")
    print("    - Prevents clickjacking attacks")
    print("    - Default: DENY")
    print()
    print("  • X-Content-Type-Options")
    print("    - Prevents MIME sniffing attacks")
    print("    - Value: nosniff")
    print()
    print("  • X-XSS-Protection")
    print("    - Legacy XSS protection")
    print("    - Value: 1; mode=block")
    print()
    print("  • Referrer-Policy")
    print("    - Controls referrer information")
    print("    - Default: strict-origin-when-cross-origin")
    print()
    print("  • Permissions-Policy")
    print("    - Controls browser features")
    print("    - Disables geolocation, camera, microphone, etc.")
    print()
    print("  • Server Header")
    print("    - Hides or customizes server information")
    print("    - Reduces information disclosure")

    print("\n⚙️  CONFIGURATION:")
    print("  • All headers are configurable via environment variables")
    print("  • Can be enabled/disabled individually")
    print("  • Development vs Production presets available")
    print("  • Validation of configuration values")

    print("\n🚀 USAGE:")
    print("  1. Update your .env file with security header settings")
    print("  2. Restart the application")
    print("  3. Security headers will be automatically applied to all responses")
    print("  4. Use this test script to verify implementation")

    print("\n📝 CONFIGURATION FILES:")
    print("  • src/configs/enviornment/security_config.py - Configuration schema")
    print("  • src/middleware/security_middleware.py - Middleware implementation")
    print("  • src/extensions/ext_security.py - Extension integration")
    print("  • .env.example - Example configuration")

    print("\n" + "=" * 80)


async def main():
    """Main test function."""
    print_security_headers_info()

    print("\n🧪 TESTING SECURITY HEADERS...")
    print("Make sure the application is running on http://localhost:5001")

    try:
        await test_security_headers()
        print("\n✅ Security headers test completed!")
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        print("Make sure the application is running and accessible.")


if __name__ == "__main__":
    asyncio.run(main())

#!/usr/bin/env python3
"""
Test script to verify that documentation endpoints work correctly
with security headers middleware.
"""

import asyncio
import logging

import httpx

# Configure logging
logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)


async def test_documentation_endpoints():
    """Test that documentation endpoints work without CSP blocking."""
    base_url = "http://localhost:5001"

    endpoints_to_test = [
        ("/docs", "Swagger UI"),
        ("/redoc", "ReDoc"),
        ("/openapi.json", "OpenAPI JSON"),
        ("/api/v1/health", "Regular API endpoint"),
    ]

    async with httpx.AsyncClient() as client:
        for endpoint, description in endpoints_to_test:
            try:
                log.info(f"Testing {description}: {endpoint}")
                response = await client.get(f"{base_url}{endpoint}")

                log.info(f"Status Code: {response.status_code}")

                # Check CSP header
                csp_header = response.headers.get("content-security-policy")
                if csp_header:
                    log.info(f"CSP Present: {csp_header[:100]}...")
                else:
                    log.info("CSP: NOT PRESENT (good for docs endpoints)")

                # Check other security headers
                security_headers = [
                    "strict-transport-security",
                    "x-frame-options",
                    "x-content-type-options",
                    "x-xss-protection",
                    "referrer-policy",
                ]

                present_security_headers = []
                for header in security_headers:
                    if response.headers.get(header):
                        present_security_headers.append(header)

                log.info(f"Other Security Headers: {len(present_security_headers)}/5 present")

                # For documentation endpoints, check if content loads
                if endpoint in ["/docs", "/redoc"]:
                    if response.status_code == 200:
                        content = response.text
                        if "swagger" in content.lower() or "redoc" in content.lower() or "openapi" in content.lower():
                            log.info("✅ Documentation content appears to be loading correctly")
                        else:
                            log.warning("⚠️  Documentation content might not be loading properly")
                    else:
                        log.error(f"❌ Documentation endpoint returned {response.status_code}")

                log.info("-" * 60)

            except Exception as e:
                log.exception(f"Error testing endpoint {endpoint}")


def print_csp_info():
    """Print information about CSP handling for documentation."""
    print("\n" + "=" * 80)
    print("CONTENT SECURITY POLICY (CSP) - DOCUMENTATION ENDPOINTS")
    print("=" * 80)

    print("\n🔍 HOW SECURITY HEADERS ARE HANDLED:")
    print("  • Regular API endpoints: Full security header protection applied")
    print("  • Documentation endpoints (/docs, /redoc): All security headers skipped")
    print("  • Production: Documentation endpoints completely disabled (404)")

    print("\n📋 DOCUMENTATION ENDPOINTS:")
    print("  • /docs - Swagger UI")
    print("  • /redoc - ReDoc")
    print("  • /openapi.json - OpenAPI specification")
    print("  • /docs/oauth2-redirect - OAuth2 redirect")

    print("\n⚙️  CONFIGURATION:")
    print("  • Development (DEBUG=true + DEPLOY_ENV=DEVELOPMENT): Docs enabled, no security headers")
    print("  • Production (DEBUG=false or DEPLOY_ENV=PRODUCTION): Docs disabled completely")
    print("  • Override: Set SECURITY_HEADERS_ENABLED=false to disable all security headers")

    print("\n🐛 TROUBLESHOOTING:")
    print("  1. If docs show blank page:")
    print("     - Check browser console for CSP violations")
    print("     - Ensure DEBUG=true in development")
    print("     - Try incognito mode")
    print("  2. If docs work but API doesn't:")
    print("     - Check CSP configuration for your frontend")
    print("     - Review browser console errors")

    print("\n🔒 SECURITY NOTES:")
    print("  • Documentation endpoints have NO security headers in development")
    print("  • Production deployments have documentation completely disabled")
    print("  • This ensures clean security configuration without exceptions")

    print("\n" + "=" * 80)


async def main():
    """Main test function."""
    print_csp_info()

    print("\n🧪 TESTING DOCUMENTATION ENDPOINTS...")
    print("Make sure the application is running on http://localhost:5001")

    try:
        await test_documentation_endpoints()
        print("\n✅ Documentation endpoint test completed!")
        print("\nIf docs are still not working:")
        print("1. Check browser console for errors")
        print("2. Try opening in incognito mode")
        print("3. Verify DEBUG=true in your .env file")
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        print("Make sure the application is running and accessible.")


if __name__ == "__main__":
    asyncio.run(main())

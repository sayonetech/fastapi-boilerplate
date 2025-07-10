#!/usr/bin/env python3
"""
Production Readiness Audit Script for Madcrow Backend

This script audits your current configuration against production best practices
and provides recommendations for security and performance improvements.
"""

import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

try:
    from configs import madcrow_config
except ImportError:
    print("❌ Error: Could not import madcrow_config. Make sure you're running from the project root.")
    sys.exit(1)


class ProductionAuditor:
    """Audits production readiness of the application configuration."""

    def __init__(self):
        self.issues = []
        self.warnings = []
        self.passed = []
        self.score = 0
        self.max_score = 0

    def audit_security(self):
        """Audit security configuration."""
        print("\n🔒 SECURITY AUDIT")
        print("=" * 50)

        # Critical: CSP Script Source
        self.max_score += 10
        if "'unsafe-inline'" in madcrow_config.SECURITY_CSP_SCRIPT_SRC:
            self.issues.append("❌ CRITICAL: CSP script-src contains 'unsafe-inline' - XSS vulnerability risk")
            print("❌ CSP Script-src: UNSAFE (contains 'unsafe-inline')")
        else:
            self.score += 10
            self.passed.append("✅ CSP Script-src: SECURE")
            print("✅ CSP Script-src: SECURE")

        # HSTS Configuration
        self.max_score += 5
        if madcrow_config.SECURITY_HSTS_ENABLED:
            if madcrow_config.SECURITY_HSTS_MAX_AGE >= 31536000:  # 1 year
                self.score += 5
                self.passed.append("✅ HSTS: Properly configured")
                print("✅ HSTS: Properly configured (1+ year max-age)")
            else:
                self.score += 3
                self.warnings.append("⚠️  HSTS max-age less than 1 year")
                print("⚠️  HSTS: Short max-age (consider 1+ year)")
        else:
            self.issues.append("❌ HSTS: Disabled")
            print("❌ HSTS: DISABLED")

        # Environment Settings
        self.max_score += 5
        if madcrow_config.DEPLOY_ENV == "PRODUCTION" and not madcrow_config.DEBUG:
            self.score += 5
            self.passed.append("✅ Environment: Production mode")
            print("✅ Environment: Production mode")
        elif madcrow_config.DEBUG:
            self.issues.append("❌ DEBUG mode enabled in production")
            print("❌ Environment: DEBUG mode enabled")
        else:
            self.warnings.append("⚠️  DEPLOY_ENV not set to PRODUCTION")
            print("⚠️  Environment: Not set to PRODUCTION")

        # Secret Key
        self.max_score += 5
        if len(madcrow_config.SECRET_KEY) >= 32:
            self.score += 5
            self.passed.append("✅ Secret Key: Adequate length")
            print("✅ Secret Key: Adequate length")
        else:
            self.issues.append("❌ Secret Key too short (< 32 characters)")
            print("❌ Secret Key: TOO SHORT")

        # CORS Configuration
        self.max_score += 3
        cors_origins = madcrow_config.web_api_cors_allow_origins
        if "*" in cors_origins:
            self.warnings.append("⚠️  CORS allows all origins (*)")
            print("⚠️  CORS: Allows all origins (*)")
        else:
            self.score += 3
            self.passed.append("✅ CORS: Restricted origins")
            print("✅ CORS: Restricted origins")

    def audit_database(self):
        """Audit database configuration."""
        print("\n🗄️  DATABASE AUDIT")
        print("=" * 50)

        # SSL/TLS for database
        self.max_score += 5
        db_extras = madcrow_config.DB_EXTRAS.lower()
        if "sslmode=require" in db_extras or "ssl" in db_extras:
            self.score += 5
            self.passed.append("✅ Database: SSL/TLS configured")
            print("✅ Database: SSL/TLS configured")
        else:
            self.warnings.append("⚠️  Database SSL/TLS not explicitly configured")
            print("⚠️  Database: SSL/TLS not explicitly configured")

        # Connection pooling
        self.max_score += 3
        if madcrow_config.SQLALCHEMY_POOL_SIZE >= 10:
            self.score += 3
            self.passed.append("✅ Database: Connection pooling configured")
            print("✅ Database: Connection pooling configured")
        else:
            self.warnings.append("⚠️  Database connection pool size might be too small")
            print("⚠️  Database: Small connection pool")

    def audit_performance(self):
        """Audit performance configuration."""
        print("\n🚀 PERFORMANCE AUDIT")
        print("=" * 50)

        # Compression
        self.max_score += 2
        if madcrow_config.API_COMPRESSION_ENABLED:
            self.score += 2
            self.passed.append("✅ Compression: Enabled")
            print("✅ Compression: Enabled")
        else:
            self.warnings.append("⚠️  API compression disabled")
            print("⚠️  Compression: Disabled")

        # Logging level
        self.max_score += 2
        if madcrow_config.LOG_LEVEL in ["INFO", "WARNING", "ERROR"]:
            self.score += 2
            self.passed.append("✅ Logging: Production level")
            print("✅ Logging: Production level")
        else:
            self.warnings.append("⚠️  Log level might be too verbose for production")
            print("⚠️  Logging: Verbose level")

    def audit_monitoring(self):
        """Audit monitoring and observability."""
        print("\n📊 MONITORING AUDIT")
        print("=" * 50)

        # Health checks
        self.max_score += 3
        # This is always enabled in our implementation
        self.score += 3
        self.passed.append("✅ Health checks: Available")
        print("✅ Health checks: Available")

        # Security headers monitoring
        self.max_score += 2
        if madcrow_config.SECURITY_HEADERS_ENABLED:
            self.score += 2
            self.passed.append("✅ Security headers: Enabled")
            print("✅ Security headers: Enabled")
        else:
            self.issues.append("❌ Security headers disabled")
            print("❌ Security headers: DISABLED")

    def generate_report(self):
        """Generate final audit report."""
        print("\n" + "=" * 60)
        print("📋 PRODUCTION READINESS AUDIT REPORT")
        print("=" * 60)

        percentage = (self.score / self.max_score) * 100 if self.max_score > 0 else 0

        print(f"\n🎯 OVERALL SCORE: {self.score}/{self.max_score} ({percentage:.1f}%)")

        if percentage >= 90:
            print("🟢 EXCELLENT - Production ready!")
        elif percentage >= 80:
            print("🟡 GOOD - Minor improvements needed")
        elif percentage >= 70:
            print("🟠 FAIR - Several improvements needed")
        else:
            print("🔴 POOR - Major improvements required before production")

        if self.issues:
            print(f"\n❌ CRITICAL ISSUES ({len(self.issues)}):")
            for issue in self.issues:
                print(f"  {issue}")

        if self.warnings:
            print(f"\n⚠️  WARNINGS ({len(self.warnings)}):")
            for warning in self.warnings:
                print(f"  {warning}")

        if self.passed:
            print(f"\n✅ PASSED CHECKS ({len(self.passed)}):")
            for passed in self.passed[:5]:  # Show first 5
                print(f"  {passed}")
            if len(self.passed) > 5:
                print(f"  ... and {len(self.passed) - 5} more")

        print("\n📚 RECOMMENDATIONS:")
        print("  1. Review docs/PRODUCTION_CHECKLIST.md for complete checklist")
        print("  2. Test security headers: uv run python test_security_headers.py")
        print("  3. Run online security tests:")
        print("     - https://securityheaders.com/")
        print("     - https://observatory.mozilla.org/")

        return percentage >= 80  # Return True if production ready

    def run_audit(self):
        """Run complete production audit."""
        print("🔍 MADCROW BACKEND - PRODUCTION READINESS AUDIT")
        print("=" * 60)
        print(f"Environment: {madcrow_config.DEPLOY_ENV}")
        print(f"Debug Mode: {madcrow_config.DEBUG}")

        self.audit_security()
        self.audit_database()
        self.audit_performance()
        self.audit_monitoring()

        return self.generate_report()


def main():
    """Main audit function."""
    auditor = ProductionAuditor()
    is_ready = auditor.run_audit()

    if not is_ready:
        print("\n⚠️  RECOMMENDATION: Address critical issues before production deployment")
        sys.exit(1)
    else:
        print("\n✅ READY: Configuration looks good for production!")
        sys.exit(0)


if __name__ == "__main__":
    main()

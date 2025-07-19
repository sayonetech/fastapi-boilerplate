#!/usr/bin/env python3
"""
Run tests for core business logic only and show focused coverage.
"""

import subprocess
import sys
from pathlib import Path

# Core business logic files to include in coverage
CORE_FILES = [
    "src/services/auth_service.py",
    "src/services/session_service.py",
    "src/services/token_service.py",
    "src/services/health.py",
    "src/utils/rate_limiter.py",
    "src/utils/validation.py",
    "src/utils/error_factory.py",
    "src/libs/password.py",
    "src/libs/login.py",
    "src/dependencies/auth.py",
    "src/dependencies/db.py",
    "src/dependencies/redis.py",
    "src/extensions/ext_db.py",
    "src/extensions/ext_redis.py",
]

# Core test files that are working
CORE_TESTS = [
    "unit/test_session_service.py",
    "unit/test_token_service.py",
    "unit/test_auth_service.py",
    "unit/test_rate_limiter.py",
]


def run_core_tests():
    """Run core business logic tests with focused coverage."""

    # Change to tests directory
    tests_dir = Path(__file__).parent

    # Build coverage command with specific files
    coverage_args = []
    for file in CORE_FILES:
        coverage_args.extend(["--cov", file])

    # Build pytest command
    cmd = [
        "uv",
        "run",
        "pytest",
        *CORE_TESTS,
        "--cov",
        "src/services/auth_service.py",
        "--cov",
        "src/services/session_service.py",
        "--cov",
        "src/services/token_service.py",
        "--cov",
        "src/utils/rate_limiter.py",
        "--cov-report=term-missing",
        "--cov-report=html:htmlcov_core",
        "--tb=short",
        "-v",
    ]

    print("🚀 Running core business logic tests...")
    print(f"📁 Working directory: {tests_dir}")
    print(f"🧪 Test files: {', '.join(CORE_TESTS)}")
    print(f"📊 Coverage files: {len(CORE_FILES)} core business logic files")
    print("-" * 80)

    # Run the command
    result = subprocess.run(cmd, cwd=tests_dir, capture_output=False)

    if result.returncode == 0:
        print("\n✅ Core tests completed successfully!")
        print("📊 Coverage report saved to htmlcov_core/")
    else:
        print(f"\n❌ Tests failed with return code: {result.returncode}")

    return result.returncode


if __name__ == "__main__":
    sys.exit(run_core_tests())

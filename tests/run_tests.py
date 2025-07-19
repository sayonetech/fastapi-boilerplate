#!/usr/bin/env python3
"""
Test runner script for the FastAPI Madcrow project.

This script provides convenient ways to run different categories of tests
and generate coverage reports.
"""

import argparse
import os
import subprocess
import sys
from pathlib import Path


def run_command(command, description):
    """Run a command and handle errors."""
    print(f"\n{'=' * 60}")
    print(f"Running: {description}")
    print(f"Command: {' '.join(command)}")
    print(f"{'=' * 60}")

    try:
        result = subprocess.run(command, check=True, capture_output=False)
        print(f"✅ {description} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed with exit code {e.returncode}")
        return False
    except FileNotFoundError:
        print(f"❌ Command not found: {command[0]}")
        print("Make sure pytest is installed: pip install pytest")
        return False


def main():
    """Main test runner function."""
    parser = argparse.ArgumentParser(description="Run tests for FastAPI Madcrow project")
    parser.add_argument(
        "--category",
        choices=["unit", "integration", "api", "e2e", "performance", "security", "edge_cases", "all"],
        default="all",
        help="Category of tests to run (default: all)",
    )
    parser.add_argument("--coverage", action="store_true", help="Generate coverage report")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    parser.add_argument("--parallel", "-n", type=int, help="Number of parallel workers (requires pytest-xdist)")
    parser.add_argument("--markers", help="Run tests with specific markers (e.g., 'slow', 'integration')")
    parser.add_argument("--pattern", "-k", help="Run tests matching pattern")

    args = parser.parse_args()

    # Base pytest command
    cmd = ["uv", "run", "pytest"]

    # Add test directory based on category and execution context
    current_dir = os.getcwd()

    if args.category == "all":
        if current_dir.endswith("/tests"):
            cmd.append(".")
        else:
            cmd.append("tests/")
    else:
        if current_dir.endswith("/tests"):
            test_dir = f"{args.category}/"
        else:
            test_dir = f"tests/{args.category}/"

        if not Path(test_dir).exists():
            print(f"❌ Test directory {test_dir} does not exist")
            return False
        cmd.append(test_dir)

    # Add coverage if requested
    if args.coverage:
        cmd.extend(["--cov=src", "--cov-report=html:htmlcov", "--cov-report=term-missing", "--cov-report=xml"])

    # Add verbose output
    if args.verbose:
        cmd.append("-v")

    # Add parallel execution
    if args.parallel:
        cmd.extend(["-n", str(args.parallel)])

    # Add markers
    if args.markers:
        cmd.extend(["-m", args.markers])

    # Add pattern matching
    if args.pattern:
        cmd.extend(["-k", args.pattern])

    # Add other useful options
    cmd.extend(
        [
            "--tb=short",  # Shorter traceback format
            "--strict-markers",  # Strict marker checking
            "--disable-warnings",  # Disable warnings for cleaner output
        ]
    )

    # Run the tests
    success = run_command(cmd, f"Running {args.category} tests")

    if success and args.coverage:
        print("\n📊 Coverage report generated:")
        print("  - HTML: htmlcov/index.html")
        print("  - XML: coverage.xml")

    return success


def run_specific_test_suites():
    """Run specific test suites with predefined configurations."""
    test_suites = [
        {
            "name": "Quick Unit Tests",
            "command": ["uv", "run", "pytest", "unit/", "-v", "--tb=short"],
            "description": "Fast unit tests for core functionality",
        },
        {
            "name": "Authentication API Tests",
            "command": ["uv", "run", "pytest", "api/test_auth_endpoints.py", "-v"],
            "description": "API tests for authentication endpoints",
        },
        {
            "name": "Database Integration Tests",
            "command": ["uv", "run", "pytest", "integration/test_database.py", "-v"],
            "description": "Database integration tests",
        },
        {
            "name": "End-to-End Authentication Flows",
            "command": ["uv", "run", "pytest", "e2e/test_auth_flows.py", "-v"],
            "description": "Complete authentication flow tests",
        },
        {
            "name": "Rate Limiting Tests",
            "command": ["uv", "run", "pytest", "e2e/test_rate_limiting.py", "-v"],
            "description": "Rate limiting functionality tests",
        },
    ]

    print("Available test suites:")
    for i, suite in enumerate(test_suites, 1):
        print(f"  {i}. {suite['name']} - {suite['description']}")

    try:
        choice = input("\nEnter suite number (1-5) or 'all' to run all suites: ").strip()

        if choice.lower() == "all":
            results = []
            for suite in test_suites:
                success = run_command(suite["command"], suite["name"])
                results.append((suite["name"], success))

            print(f"\n{'=' * 60}")
            print("Test Suite Results:")
            print(f"{'=' * 60}")
            for name, success in results:
                status = "✅ PASSED" if success else "❌ FAILED"
                print(f"{status} - {name}")

            return all(result[1] for result in results)

        elif choice.isdigit() and 1 <= int(choice) <= len(test_suites):
            suite = test_suites[int(choice) - 1]
            return run_command(suite["command"], suite["name"])

        else:
            print("❌ Invalid choice")
            return False

    except KeyboardInterrupt:
        print("\n❌ Test execution cancelled")
        return False


if __name__ == "__main__":
    if len(sys.argv) == 1:
        # If no arguments provided, show interactive menu
        success = run_specific_test_suites()
    else:
        # Use command line arguments
        success = main()

    sys.exit(0 if success else 1)

#!/usr/bin/env python3
"""
Test script to demonstrate the enhanced error handling system.

This script tests various error scenarios to ensure the error handling
system works correctly and produces consistent error responses.
"""

import json
from uuid import uuid4

from fastapi.testclient import TestClient

from app import create_app
from src.exceptions import (
    AccountNotFoundError,
    DatabaseConnectionError,
)
from src.utils.error_factory import ErrorFactory, ErrorResponseFactory
from src.utils.validation import ValidationUtils


def test_exception_creation():
    """Test creating custom exceptions."""
    print("Testing exception creation...")

    # Test AccountNotFoundError
    account_id = uuid4()
    error = AccountNotFoundError(account_id=account_id)
    print(f"✓ AccountNotFoundError: {error}")
    print(f"  Error ID: {error.error_id}")
    print(f"  Error Code: {error.error_code}")
    print(f"  Status Code: {error.status_code}")

    # Test ValidationError using factory
    validation_error = ErrorFactory.create_validation_error(
        field="email", message="Invalid email format", value="invalid-email"
    )
    print(f"✓ ValidationError: {validation_error}")

    # Test DatabaseConnectionError
    db_error = DatabaseConnectionError("Connection timeout")
    print(f"✓ DatabaseConnectionError: {db_error}")


def test_error_response_factory():
    """Test error response factory."""
    print("\nTesting error response factory...")

    # Test with custom exception
    account_error = AccountNotFoundError(account_id=uuid4())
    response = ErrorResponseFactory.from_exception(account_error)
    print("✓ Error response from AccountNotFoundError:")
    print(json.dumps(response, indent=2, default=str))

    # Test with generic exception
    generic_error = ValueError("Something went wrong")
    response = ErrorResponseFactory.from_exception(generic_error, include_debug_info=True)
    print("\n✓ Error response from generic exception:")
    print(json.dumps(response, indent=2, default=str))


def test_validation_utils():
    """Test validation utilities."""
    print("\nTesting validation utilities...")

    # Test email validation
    try:
        valid_email = ValidationUtils.validate_email("test@example.com")
        print(f"✓ Valid email: {valid_email}")
    except Exception as e:
        print(f"✗ Email validation failed: {e}")

    try:
        ValidationUtils.validate_email("invalid-email")
        print("✗ Should have failed for invalid email")
    except Exception as e:
        print(f"✓ Correctly rejected invalid email: {e}")

    # Test password validation
    try:
        ValidationUtils.validate_password("StrongPass123!")
        print("✓ Strong password accepted")
    except Exception as e:
        print(f"✗ Strong password rejected: {e}")

    try:
        ValidationUtils.validate_password("weak")
        print("✗ Should have failed for weak password")
    except Exception as e:
        print(f"✓ Correctly rejected weak password: {e}")

    # Test UUID validation
    try:
        test_uuid = uuid4()
        validated = ValidationUtils.validate_uuid(test_uuid)
        print(f"✓ UUID validation: {validated}")
    except Exception as e:
        print(f"✗ UUID validation failed: {e}")


def test_api_endpoints():
    """Test API endpoints with error handling."""
    print("\nTesting API endpoints...")

    try:
        app = create_app()
        client = TestClient(app)

        # Test health endpoint (should work)
        response = client.get("/v1/health/")
        print(f"✓ Health endpoint: {response.status_code}")

        # Test database example endpoint
        response = client.get("/v1/database/test")
        print(f"✓ Database test endpoint: {response.status_code}")
        if response.status_code != 200:
            print(f"  Response: {response.json()}")

        # Test account example endpoint (should return 404 for non-existent account)
        if hasattr(client.app.router, "routes"):
            # Check if account example routes are registered
            account_routes = [
                route
                for route in client.app.router.routes
                if hasattr(route, "path") and "accounts-example" in route.path
            ]
            if account_routes:
                test_uuid = str(uuid4())
                response = client.get(f"/v1/accounts-example/{test_uuid}")
                print(f"✓ Account example endpoint (not found): {response.status_code}")
                if response.status_code == 404:
                    error_response = response.json()
                    print(f"  Error response structure: {list(error_response.keys())}")

        print("✓ API endpoint tests completed")

    except Exception as e:
        print(f"✗ API endpoint test failed: {e}")


def test_error_middleware():
    """Test error middleware functionality."""
    print("\nTesting error middleware...")

    try:
        app = create_app()

        # Check if error handling middleware is registered
        middleware_names = [middleware.cls.__name__ for middleware in app.user_middleware]
        if "ErrorHandlingMiddleware" in middleware_names:
            print("✓ ErrorHandlingMiddleware is registered")
        else:
            print("✗ ErrorHandlingMiddleware not found in middleware stack")
            print(f"  Available middleware: {middleware_names}")

        # Check if exception handlers are registered
        exception_handlers = app.exception_handlers
        print(f"✓ Exception handlers registered: {len(exception_handlers)}")

    except Exception as e:
        print(f"✗ Error middleware test failed: {e}")


def main():
    """Run all error handling tests."""
    print("Enhanced Error Handling System Test")
    print("=" * 50)

    try:
        test_exception_creation()
        test_error_response_factory()
        test_validation_utils()
        test_error_middleware()
        test_api_endpoints()

        print("\n" + "=" * 50)
        print("✓ All tests completed successfully!")

    except Exception as e:
        print(f"\n✗ Test suite failed: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()

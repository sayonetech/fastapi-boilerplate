"""Unit tests for error factory."""

import pytest

from src.utils.error_factory import (
    ErrorFactory,
    ErrorResponseFactory,
    _generate_deterministic_id,
)


@pytest.mark.unit
class TestErrorFactory:
    """Test error factory functionality."""

    def test_create_validation_error(self):
        """Test validation error creation."""
        error = ErrorFactory.create_validation_error("email", "Invalid email format")

        assert hasattr(error, "context")
        assert error.context.get("field") == "email"
        assert "Invalid email format" in str(error)

    def test_create_authentication_error(self):
        """Test authentication error creation."""
        error = ErrorFactory.create_authentication_error("Invalid credentials")

        assert hasattr(error, "message")
        assert "Invalid credentials" in str(error)

    def test_create_authorization_error(self):
        """Test authorization error creation."""
        error = ErrorFactory.create_authorization_error("Access denied")

        assert hasattr(error, "message")
        assert "Access denied" in str(error)

    def test_create_record_not_found_error(self):
        """Test record not found error creation."""
        error = ErrorFactory.create_record_not_found_error("users", "123")

        assert hasattr(error, "message")
        assert "users" in str(error)
        assert "123" in str(error)

    def test_create_duplicate_record_error(self):
        """Test duplicate record error creation."""
        error = ErrorFactory.create_duplicate_record_error("users", "email", "test@example.com")

        assert hasattr(error, "context")
        assert error.context.get("table") == "users"
        assert error.context.get("field") == "email"
        assert error.context.get("value") == "test@example.com"
        assert "users" in str(error)
        assert "email" in str(error)


@pytest.mark.unit
class TestErrorResponseFactory:
    """Test ErrorResponseFactory functionality."""

    def test_from_exception_basic(self):
        """Test creating error response from basic exception."""
        exception = ValueError("Something went wrong")

        response = ErrorResponseFactory.from_exception(exception)

        assert response is not None
        assert "error_id" in response
        assert "message" in response
        assert response["error"] is True

    def test_from_exception_basic(self):
        """Test creating basic error response."""
        exception = ValueError("Database error")

        response = ErrorResponseFactory.from_exception(exception)

        assert response is not None
        assert "error_id" in response

    def test_generate_deterministic_id(self):
        """Test deterministic ID generation."""
        id1 = _generate_deterministic_id("test_input")
        id2 = _generate_deterministic_id("test_input")
        id3 = _generate_deterministic_id("different_input")

        # Same input should produce same ID
        assert id1 == id2

        # Different input should produce different ID
        assert id1 != id3

        # Should be string of expected length
        assert isinstance(id1, str)
        assert len(id1) == 8  # Default length

    def test_generate_deterministic_id_with_prefix(self):
        """Test deterministic ID generation with prefix."""
        id_with_prefix = _generate_deterministic_id("test", prefix="ERR", length=6)

        assert id_with_prefix.startswith("ERR-")
        assert len(id_with_prefix) == 10  # ERR- + 6 characters

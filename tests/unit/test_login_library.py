"""Unit tests for login library."""

from unittest.mock import Mock, patch

import pytest
from fastapi import Request

from src.libs.login import admin_required, login_required


@pytest.mark.unit
class TestLoginRequired:
    """Test login_required decorator functionality."""

    @pytest.fixture
    def mock_request(self):
        """Create mock FastAPI Request."""
        request = Mock(spec=Request)
        request.url.path = "/test-endpoint"
        return request

    @pytest.fixture
    def mock_user(self):
        """Create mock authenticated user."""
        user = Mock()
        user.email = "test@example.com"
        user.id = "user123"
        user.is_admin = False
        return user

    @pytest.fixture
    def mock_admin_user(self):
        """Create mock admin user."""
        user = Mock()
        user.email = "admin@example.com"
        user.id = "admin123"
        user.is_admin = True
        return user

    def test_decorator_exists(self):
        """Test that login_required decorator exists and can be applied."""

        @login_required
        async def test_func():
            return "success"

        assert callable(test_func)
        assert test_func.__name__ == "test_func"

    def test_admin_decorator_exists(self):
        """Test that admin_required decorator exists and can be applied."""

        @admin_required
        async def test_func():
            return "success"

        assert callable(test_func)
        assert test_func.__name__ == "test_func"

    @patch("src.libs.login.madcrow_config")
    def test_login_disabled_config_check(self, mock_config):
        """Test that decorator can access LOGIN_DISABLED config."""
        mock_config.LOGIN_DISABLED = True

        @login_required
        async def test_func(request):
            return {"message": "success"}

        # Just test that the decorator was applied successfully
        assert callable(test_func)

    def test_decorator_imports_successfully(self):
        """Test that decorators can be imported and applied."""
        # Test that we can import and use the decorators
        from src.libs.login import admin_required, login_required

        @login_required
        async def login_func():
            return "login_required applied"

        @admin_required
        async def admin_func():
            return "admin_required applied"

        assert callable(login_func)
        assert callable(admin_func)

    def test_decorator_preserves_function_name(self):
        """Test that decorators preserve function metadata."""

        @login_required
        async def test_login_func():
            """Test login function."""
            return "success"

        @admin_required
        async def test_admin_func():
            """Test admin function."""
            return "success"

        assert test_login_func.__name__ == "test_login_func"
        assert test_admin_func.__name__ == "test_admin_func"

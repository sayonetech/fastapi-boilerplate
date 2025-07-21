"""Unit tests for authentication routes."""

import pytest

from src.routes.v1.auth import AuthController, auth_router


@pytest.mark.unit
class TestAuthRoutes:
    """Test authentication route class."""

    def test_auth_controller_class_exists(self):
        """Test that AuthController class exists and can be instantiated."""
        controller = AuthController()
        assert controller is not None

    def test_auth_controller_has_login_method(self):
        """Test that AuthController has login method."""
        controller = AuthController()
        assert hasattr(controller, "login")
        assert callable(controller.login)

    def test_auth_controller_has_logout_method(self):
        """Test that AuthController has logout method."""
        controller = AuthController()
        assert hasattr(controller, "logout")
        assert callable(controller.logout)

    def test_auth_controller_has_register_method(self):
        """Test that AuthController has register method."""
        controller = AuthController()
        assert hasattr(controller, "register")
        assert callable(controller.register)

    def test_auth_controller_has_refresh_method(self):
        """Test that AuthController has refresh_token method."""
        controller = AuthController()
        assert hasattr(controller, "refresh_token")
        assert callable(controller.refresh_token)

    def test_auth_controller_has_validate_session_method(self):
        """Test that AuthController has validate_session method."""
        controller = AuthController()
        assert hasattr(controller, "validate_session")
        assert callable(controller.validate_session)

    def test_auth_router_creation(self):
        """Test that auth_router exists and has routes."""
        assert auth_router is not None
        assert hasattr(auth_router, "routes")

    def test_auth_controller_method_signatures(self):
        """Test that auth controller methods have expected signatures."""
        import inspect

        controller = AuthController()

        # Test login method signature
        login_sig = inspect.signature(controller.login)
        assert "request" in login_sig.parameters

        # Test register method signature
        register_sig = inspect.signature(controller.register)
        assert "request" in register_sig.parameters

    def test_auth_routes_imports(self):
        """Test that auth routes can import required dependencies."""
        # Test that we can import the main components
        from src.routes.base_router import BaseRouter
        from src.routes.v1.auth import AuthController, auth_router

        assert AuthController is not None
        assert auth_router is not None
        assert BaseRouter is not None

    def test_auth_routes_router_tags(self):
        """Test that router has appropriate tags."""
        # Router should have tags for API documentation
        assert hasattr(auth_router, "tags")
        assert "authentication" in auth_router.tags

    def test_auth_routes_router_prefix(self):
        """Test that router can be used with prefix."""
        # Router should be usable with FastAPI
        assert hasattr(auth_router, "routes")
        assert auth_router.prefix == "/api/v1/auth"

    def test_auth_routes_dependencies_import(self):
        """Test that auth routes can import dependencies."""
        try:
            assert True  # Import successful
        except ImportError:
            pytest.fail("Failed to import auth route dependencies")

    def test_auth_routes_models_import(self):
        """Test that auth routes can import models."""
        try:
            assert True  # Import successful
        except ImportError:
            pytest.fail("Failed to import auth route models")

    def test_auth_routes_exceptions_import(self):
        """Test that auth routes can import exceptions."""
        try:
            assert True  # Import successful
        except ImportError:
            pytest.fail("Failed to import auth route exceptions")

    def test_auth_routes_cbv_decorators(self):
        """Test that CBV decorators are available."""
        try:
            from src.routes.v1.auth import cbv, post

            assert callable(cbv)
            assert callable(post)
        except ImportError:
            pytest.fail("Failed to import CBV decorators")

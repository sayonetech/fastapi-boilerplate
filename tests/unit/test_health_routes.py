"""Unit tests for health routes."""

import pytest

from src.routes.v1.health import HealthController, health_router


@pytest.mark.unit
class TestHealthRoutes:
    """Test health check route class."""

    def test_health_controller_class_exists(self):
        """Test that HealthController class exists and can be instantiated."""
        controller = HealthController()
        assert controller is not None

    def test_health_controller_has_health_check_method(self):
        """Test that HealthController has health_check method."""
        controller = HealthController()
        assert hasattr(controller, "health_check")
        assert callable(controller.health_check)

    def test_health_controller_has_detailed_health_method(self):
        """Test that HealthController has liveness_check method (detailed health check)."""
        controller = HealthController()
        assert hasattr(controller, "liveness_check")
        assert callable(controller.liveness_check)

    def test_health_router_creation(self):
        """Test that health_router exists and has routes."""
        assert health_router is not None
        assert hasattr(health_router, "routes")

    def test_health_routes_imports(self):
        """Test that health routes can import required dependencies."""
        from src.routes.v1.health import HealthController, health_router

        assert HealthController is not None
        assert health_router is not None

    def test_health_routes_dependencies_import(self):
        """Test that health routes can import dependencies."""
        try:
            from src.routes.v1.health import HealthServiceDep

            assert HealthServiceDep is not None
        except ImportError:
            pytest.fail("Failed to import health route dependencies")

    def test_health_controller_method_signatures(self):
        """Test that health controller methods have expected signatures."""
        import inspect

        controller = HealthController()

        # Test health_check method signature
        health_sig = inspect.signature(controller.health_check)
        assert "health_service" in health_sig.parameters

    def test_health_routes_cbv_integration(self):
        """Test that health routes integrate with CBV pattern."""
        try:
            from src.routes.v1.health import cbv, get

            assert callable(cbv)
            assert callable(get)
        except ImportError:
            pytest.fail("Failed to import CBV decorators for health routes")

    def test_health_router_configuration(self):
        """Test health router configuration."""
        assert health_router.prefix == "/api/v1/health"
        assert "health" in health_router.tags

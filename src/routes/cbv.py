"""Class-Based Views implementation for FastAPI routers."""

import inspect
import logging
from collections.abc import Callable

from fastapi import APIRouter
from fastapi.routing import APIRoute

logger = logging.getLogger(__name__)


class CBV:
    """Class-Based View decorator for FastAPI routers."""

    def __init__(self, router: APIRouter):
        """
        Initialize CBV with a router.

        Args:
            router: FastAPI router instance
        """
        self.router = router
        self._cbv_routes: list[APIRoute] = []

    def __call__(self, cls: type) -> type:
        """
        Decorator to convert a class to class-based views.

        Args:
            cls: Class to convert to CBV

        Returns:
            Modified class with routes registered
        """
        return self._cbv(cls)

    def _cbv(self, cls: type) -> type:
        """
        Convert class methods to FastAPI routes.

        Args:
            cls: Class to process

        Returns:
            Modified class
        """
        # Get all methods that should be converted to routes
        route_methods = self._get_route_methods(cls)

        # Process each route method
        for method_name, method in route_methods.items():
            self._process_route_method(cls, method_name, method)

        return cls

    def _get_route_methods(self, cls: type) -> dict[str, Callable]:
        """
        Get all methods that should be converted to routes.

        Args:
            cls: Class to inspect

        Returns:
            Dictionary of method names and methods
        """
        route_methods = {}

        for name, method in inspect.getmembers(cls, predicate=inspect.isfunction):
            # Skip private methods and special methods
            if name.startswith("_"):
                continue

            # Check if method has route decorators
            if hasattr(method, "_route_info"):
                route_methods[name] = method

        return route_methods

    def _process_route_method(self, cls: type, method_name: str, method: Callable) -> None:
        """
        Process a single route method and register it with the router.

        Args:
            cls: Class containing the method
            method_name: Name of the method
            method: Method to process
        """
        route_info = method._route_info

        # Create a wrapper function that instantiates the class
        def create_route_handler(original_method: Callable) -> Callable:
            async def route_handler(*args, **kwargs):
                # Get the class instance
                instance = cls()

                # Call the original method on the instance
                if inspect.iscoroutinefunction(original_method):
                    return await original_method(instance, *args, **kwargs)
                else:
                    return original_method(instance, *args, **kwargs)

            # Copy metadata from original method
            route_handler.__name__ = original_method.__name__
            route_handler.__doc__ = original_method.__doc__

            # Copy signature for dependency injection
            sig = inspect.signature(original_method)
            # Remove 'self' parameter from signature
            params = list(sig.parameters.values())[1:]  # Skip 'self'
            new_sig = sig.replace(parameters=params)
            route_handler.__signature__ = new_sig

            return route_handler

        # Create the route handler
        handler = create_route_handler(method)

        # Register the route with the router
        self.router.add_api_route(
            path=route_info["path"], endpoint=handler, methods=route_info["methods"], **route_info.get("kwargs", {})
        )

        # Register route-controller mapping for protection middleware
        self._register_route_protection_mapping(cls, method_name, route_info)

    def _register_route_protection_mapping(self, cls: type, method_name: str, route_info: dict) -> None:
        """
        Register route-controller mapping for the protection system.

        Args:
            cls: Controller class
            method_name: Method name
            route_info: Route information dictionary
        """
        try:
            from .protection import register_route_controller_mapping

            # Build full route path (including router prefix)
            router_prefix = getattr(self.router, "prefix", "")
            route_path = route_info["path"]
            full_path = f"{router_prefix}{route_path}".rstrip("/") or "/"

            # Register mapping for each HTTP method
            for method in route_info["methods"]:
                register_route_controller_mapping(full_path, method.upper(), cls, method_name)

        except ImportError:
            # Protection system not available, skip registration
            logger.debug("Protection system not available, skipping route registration")
        except Exception as e:
            logger.warning(f"Failed to register route protection mapping: {e}")


def route(path: str, methods: list[str] | None = None, **kwargs) -> Callable:
    """
    Decorator to mark a method as a route.

    Args:
        path: Route path
        methods: HTTP methods (default: ["GET"])
        **kwargs: Additional route parameters

    Returns:
        Decorated method
    """
    if methods is None:
        methods = ["GET"]

    def decorator(func: Callable) -> Callable:
        func._route_info = {"path": path, "methods": methods, "kwargs": kwargs}
        return func

    return decorator


def get(path: str, **kwargs) -> Callable:
    """GET route decorator."""
    return route(path, methods=["GET"], **kwargs)


def post(path: str, **kwargs) -> Callable:
    """POST route decorator."""
    return route(path, methods=["POST"], **kwargs)


def put(path: str, **kwargs) -> Callable:
    """PUT route decorator."""
    return route(path, methods=["PUT"], **kwargs)


def patch(path: str, **kwargs) -> Callable:
    """PATCH route decorator."""
    return route(path, methods=["PATCH"], **kwargs)


def delete(path: str, **kwargs) -> Callable:
    """DELETE route decorator."""
    return route(path, methods=["DELETE"], **kwargs)


# Convenience function to create CBV
def cbv(router: APIRouter) -> CBV:
    """
    Create a class-based view decorator.

    Args:
        router: FastAPI router instance

    Returns:
        CBV decorator
    """
    return CBV(router)

"""Controller protection system for class-level and method-level authentication."""

import logging
from enum import Enum
from typing import Any, ClassVar

logger = logging.getLogger(__name__)


class ProtectionLevel(Enum):
    """Protection levels for controllers and methods."""

    NONE = "none"  # No protection required
    REQUIRED = "required"  # Authentication required
    INHERIT = "inherit"  # Inherit from class-level setting


class ProtectedController:
    """
    Base class for controllers that need authentication protection.

    This class provides a declarative way to specify protection requirements
    at the controller level, which can be overridden at the method level.

    Usage:
        @cbv(router)
        class MyController(ProtectedController):
            protected = True  # All methods require authentication by default

            @get("/public")
            @no_protection  # Override class-level protection
            async def public_endpoint(self): ...

            @get("/private")
            async def private_endpoint(self): ...  # Uses class-level protection
    """

    # Class-level protection setting
    protected: ClassVar[bool] = False

    def __init_subclass__(cls, **kwargs):
        """
        Initialize subclass with protection metadata.

        This method is called when a class inherits from ProtectedController
        and sets up the necessary metadata for the protection system.
        """
        super().__init_subclass__(**kwargs)

        # Store protection metadata on the class
        cls._protection_metadata = {
            "class_protected": getattr(cls, "protected", False),
            "controller_name": cls.__name__,
            "methods": {},
        }

        logger.debug(f"Registered protected controller: {cls.__name__} (protected={cls.protected})")


def protected_controller(protected: bool = True):
    """
    Class decorator to mark a controller as protected.

    This is an alternative to inheriting from ProtectedController.

    Args:
        protected: Whether the controller should be protected by default

    Usage:
        @protected_controller(True)
        @cbv(router)
        class MyController:
            @get("/endpoint")
            async def my_endpoint(self): ...
    """

    def decorator(cls: type) -> type:
        # Add protection metadata to the class
        cls.protected = protected
        cls._protection_metadata = {
            "class_protected": protected,
            "controller_name": cls.__name__,
            "methods": {},
        }

        logger.debug(f"Marked controller as protected: {cls.__name__} (protected={protected})")
        return cls

    return decorator


def no_protection(func):
    """
    Method decorator to explicitly disable protection for a specific method.

    This overrides class-level protection settings.

    Usage:
        @cbv(router)
        class MyController(ProtectedController):
            protected = True

            @get("/public")
            @no_protection
            async def public_endpoint(self): ...
    """
    func._protection_level = ProtectionLevel.NONE
    func._protection_override = True
    logger.debug(f"Marked method as unprotected: {func.__name__}")
    return func


def require_protection(func):
    """
    Method decorator to explicitly require protection for a specific method.

    This can be used to require authentication even if the class-level
    protection is disabled.

    Usage:
        @cbv(router)
        class MyController:  # No class-level protection
            @get("/private")
            @require_protection
            async def private_endpoint(self): ...
    """
    func._protection_level = ProtectionLevel.REQUIRED
    func._protection_override = True
    logger.debug(f"Marked method as protected: {func.__name__}")
    return func


def get_controller_protection_info(controller_class: type) -> dict[str, Any]:
    """
    Get protection information for a controller class.

    Args:
        controller_class: The controller class to inspect

    Returns:
        Dictionary containing protection metadata
    """
    # Check if class has protection metadata
    if hasattr(controller_class, "_protection_metadata"):
        return controller_class._protection_metadata

    # Check if class inherits from ProtectedController or has protected attribute
    class_protected = getattr(controller_class, "protected", False)

    # Check if class is a subclass of ProtectedController
    is_protected_subclass = hasattr(controller_class, "__mro__") and any(
        cls.__name__ == "ProtectedController" for cls in controller_class.__mro__
    )

    return {
        "class_protected": class_protected or is_protected_subclass,
        "controller_name": controller_class.__name__,
        "methods": {},
        "is_protected_subclass": is_protected_subclass,
    }


def get_method_protection_level(method, class_protected: bool = False) -> ProtectionLevel:
    """
    Determine the protection level for a specific method.

    Args:
        method: The method to check
        class_protected: Whether the class is protected by default

    Returns:
        ProtectionLevel indicating the required protection
    """
    # Check for explicit method-level protection override
    if hasattr(method, "_protection_override") and method._protection_override:
        return getattr(method, "_protection_level", ProtectionLevel.INHERIT)

    # Check for login_required decorator
    if hasattr(method, "_login_required"):
        return ProtectionLevel.REQUIRED

    # Use class-level setting
    if class_protected:
        return ProtectionLevel.REQUIRED
    else:
        return ProtectionLevel.NONE


def is_method_protected(method, controller_class: type) -> bool:
    """
    Check if a specific method requires protection.

    Args:
        method: The method to check
        controller_class: The controller class containing the method

    Returns:
        True if the method requires authentication, False otherwise
    """
    controller_info = get_controller_protection_info(controller_class)
    class_protected = controller_info.get("class_protected", False)

    protection_level = get_method_protection_level(method, class_protected)

    return protection_level == ProtectionLevel.REQUIRED


# Registry to store route-to-controller mappings
_route_controller_registry: dict[str, dict[str, Any]] = {}


def register_route_controller_mapping(
    route_path: str, http_method: str, controller_class: type, method_name: str
) -> None:
    """
    Register a mapping between a route and its controller.

    This is called during route registration to build the mapping
    that the middleware will use.

    Args:
        route_path: The route path (e.g., "/api/v1/users")
        http_method: HTTP method (e.g., "GET", "POST")
        controller_class: The controller class
        method_name: The method name in the controller
    """
    route_key = f"{http_method}:{route_path}"

    _route_controller_registry[route_key] = {
        "controller_class": controller_class,
        "method_name": method_name,
        "controller_name": controller_class.__name__,
        "protection_info": get_controller_protection_info(controller_class),
    }

    logger.debug(f"Registered route mapping: {route_key} -> {controller_class.__name__}.{method_name}")


def get_route_protection_info(route_path: str, http_method: str) -> dict[str, Any] | None:
    """
    Get protection information for a specific route.

    Args:
        route_path: The route path
        http_method: HTTP method

    Returns:
        Protection information dictionary or None if route not found
    """
    route_key = f"{http_method}:{route_path}"
    return _route_controller_registry.get(route_key)


def get_all_protected_routes() -> dict[str, dict[str, Any]]:
    """
    Get all routes that require protection.

    Returns:
        Dictionary mapping route keys to protection information
    """
    protected_routes = {}

    for route_key, route_info in _route_controller_registry.items():
        controller_class = route_info["controller_class"]
        method_name = route_info["method_name"]

        # Get the actual method from the controller
        if hasattr(controller_class, method_name):
            method = getattr(controller_class, method_name)
            if is_method_protected(method, controller_class):
                protected_routes[route_key] = route_info

    return protected_routes


def clear_route_registry() -> None:
    """Clear the route registry. Useful for testing."""
    global _route_controller_registry
    _route_controller_registry.clear()
    logger.debug("Cleared route controller registry")

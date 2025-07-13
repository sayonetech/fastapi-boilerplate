"""Event handlers and registration system.

This module provides decorators and utilities for registering event handlers
that respond to specific events in the system.
"""

import logging
from collections.abc import Callable
from functools import wraps
from typing import Any

from .signals import madcrow_signals

logger = logging.getLogger(__name__)


class EventHandlerRegistry:
    """Registry for managing event handlers."""

    def __init__(self) -> None:
        """Initialize the handler registry."""
        self._handlers: dict[str, list[Callable]] = {}

    def register(self, signal_name: str, handler: Callable, weak: bool = True, sender: Any | None = None) -> None:
        """
        Register an event handler for a specific signal.

        Args:
            signal_name: Name of the signal to listen for
            handler: Handler function to register
            weak: Whether to use weak references (default: True)
            sender: Optional sender to filter by
        """
        try:
            # Convert underscores to hyphens for signal lookup
            signal_key = signal_name.replace("_", "-")

            # Get the signal from namespace
            if signal_key not in madcrow_signals:
                raise ValueError(f"Signal '{signal_name}' not found")

            signal = madcrow_signals[signal_key]

            # Connect the handler to the signal
            # If sender is None, don't pass it to connect() so it listens to all senders
            if sender is None:
                signal.connect(handler, weak=weak)
            else:
                signal.connect(handler, sender=sender, weak=weak)

            # Track the handler in our registry
            if signal_name not in self._handlers:
                self._handlers[signal_name] = []
            self._handlers[signal_name].append(handler)

            logger.debug(
                f"Registered handler '{handler.__name__}' for signal '{signal_name}'",
                extra={
                    "signal_name": signal_name,
                    "handler_name": handler.__name__,
                    "sender": str(sender) if sender else None,
                },
            )

        except Exception as e:
            logger.exception(f"Failed to register handler '{handler.__name__}' for signal '{signal_name}'")
            raise

    def unregister(self, signal_name: str, handler: Callable) -> None:
        """
        Unregister an event handler.

        Args:
            signal_name: Name of the signal
            handler: Handler function to unregister
        """
        try:
            # Convert underscores to hyphens for signal lookup
            signal_key = signal_name.replace("_", "-")

            if signal_key in madcrow_signals:
                signal = madcrow_signals[signal_key]
                signal.disconnect(handler)

                # Remove from our registry
                if signal_name in self._handlers:
                    try:
                        self._handlers[signal_name].remove(handler)
                        if not self._handlers[signal_name]:
                            del self._handlers[signal_name]
                    except ValueError:
                        pass  # Handler wasn't in the list

                logger.debug(f"Unregistered handler '{handler.__name__}' from signal '{signal_name}'")

        except Exception as e:
            logger.exception(f"Failed to unregister handler '{handler.__name__}' from signal '{signal_name}'")

    def get_handlers(self, signal_name: str) -> list[Callable]:
        """
        Get all handlers for a specific signal.

        Args:
            signal_name: Name of the signal

        Returns:
            list[Callable]: List of registered handlers
        """
        return self._handlers.get(signal_name, [])

    def get_all_handlers(self) -> dict[str, list[Callable]]:
        """
        Get all registered handlers.

        Returns:
            dict[str, list[Callable]]: Dictionary of signal names to handlers
        """
        return self._handlers.copy()

    def clear(self) -> None:
        """Clear all registered handlers."""
        # Create a copy of the items to avoid dictionary changed size during iteration
        handlers_copy = list(self._handlers.items())
        for signal_name, handlers in handlers_copy:
            for handler in handlers:
                self.unregister(signal_name, handler)
        self._handlers.clear()


# Global handler registry
_handler_registry: EventHandlerRegistry | None = None


def get_handler_registry() -> EventHandlerRegistry:
    """
    Get the global handler registry.

    Returns:
        EventHandlerRegistry: The global handler registry
    """
    global _handler_registry
    if _handler_registry is None:
        _handler_registry = EventHandlerRegistry()
    return _handler_registry


def on_event(signal_name: str, weak: bool = True, sender: Any | None = None) -> Callable[[Callable], Callable]:
    """
    Decorator to register a function as an event handler.

    Args:
        signal_name: Name of the signal to listen for
        weak: Whether to use weak references (default: True)
        sender: Optional sender to filter by

    Returns:
        Callable: Decorator function

    Example:
        @on_event('user_logged_in')
        def handle_user_login(sender, **context):
            print(f"User {context['user_id']} logged in")
    """

    def decorator(func: Callable) -> Callable:
        # Register the handler
        registry = get_handler_registry()
        registry.register(signal_name, func, weak=weak, sender=sender)

        # Mark the function as an event handler
        func._event_handler = True
        func._signal_name = signal_name

        @wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)

        return wrapper

    return decorator


def register_handler(signal_name: str, handler: Callable, weak: bool = True, sender: Any | None = None) -> None:
    """
    Register an event handler function.

    Args:
        signal_name: Name of the signal to listen for
        handler: Handler function to register
        weak: Whether to use weak references (default: True)
        sender: Optional sender to filter by
    """
    registry = get_handler_registry()
    registry.register(signal_name, handler, weak=weak, sender=sender)


def unregister_handler(signal_name: str, handler: Callable) -> None:
    """
    Unregister an event handler function.

    Args:
        signal_name: Name of the signal
        handler: Handler function to unregister
    """
    registry = get_handler_registry()
    registry.unregister(signal_name, handler)


def clear_all_handlers() -> None:
    """Clear all registered event handlers."""
    registry = get_handler_registry()
    registry.clear()


# Convenience decorators for common events
def on_user_login(weak: bool = True, sender: Any | None = None):
    """Decorator for user login event handlers."""
    return on_event("user_logged_in", weak=weak, sender=sender)


def on_user_logout(weak: bool = True, sender: Any | None = None):
    """Decorator for user logout event handlers."""
    return on_event("user_logged_out", weak=weak, sender=sender)


def on_login_failed(weak: bool = True, sender: Any | None = None):
    """Decorator for login failed event handlers."""
    return on_event("login_failed", weak=weak, sender=sender)


def on_user_registered(weak: bool = True, sender: Any | None = None):
    """Decorator for user registration event handlers."""
    return on_event("user_registered", weak=weak, sender=sender)

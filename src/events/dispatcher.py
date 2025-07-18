"""Event dispatcher for the event system.

This module provides the centralized event dispatcher that handles
emitting events and managing the event flow throughout the application.
"""

import logging
from typing import Any

from blinker import Signal

from .models import (
    BaseEventContext,
    LoginEventContext,
    LoginFailedEventContext,
    LogoutEventContext,
    RegistrationEventContext,
)
from .signals import madcrow_signals

logger = logging.getLogger(__name__)


class EventDispatcher:
    """Centralized event dispatcher for managing application events."""

    def __init__(self) -> None:
        """Initialize the event dispatcher."""
        self._namespace = madcrow_signals
        self._event_count = 0

    def emit(self, signal_name: str, sender: Any | None = None, **context: Any) -> None:
        """
        Emit an event with the given signal name and context.

        Args:
            signal_name: Name of the signal to emit
            sender: Optional sender object (defaults to self)
            **context: Event context data

        Raises:
            ValueError: If signal_name is not found
        """
        try:
            # Get the signal from our namespace
            signal = self._get_signal(signal_name)

            # Use self as sender if none provided
            if sender is None:
                sender = self

            # Log the event emission
            self._event_count += 1
            logger.debug(
                f"Emitting event '{signal_name}' (#{self._event_count})",
                extra={
                    "signal_name": signal_name,
                    "sender": str(sender),
                    "context_keys": list(context.keys()),
                    "event_count": self._event_count,
                },
            )

            # Emit the signal - let Blinker handle the calling
            # We'll catch any exceptions that bubble up
            signal.send(sender, **context)

            logger.debug(f"Event '{signal_name}' emitted successfully")

        except Exception as e:
            logger.exception(
                f"Failed to emit event '{signal_name}'",
                extra={
                    "signal_name": signal_name,
                    "error": str(e),
                    "context": context,
                },
            )
            # Don't re-raise to prevent event emission from breaking the main flow

    def emit_typed(self, signal_name: str, context: BaseEventContext, sender: Any | None = None) -> None:
        """
        Emit an event with a typed context model.

        Args:
            signal_name: Name of the signal to emit
            context: Typed event context model
            sender: Optional sender object
        """
        # Convert Pydantic model to dict for signal emission
        context_dict = context.model_dump()
        self.emit(signal_name, sender=sender, **context_dict)

    def _get_signal(self, signal_name: str) -> Signal:
        """
        Get a signal by name from the namespace.

        Args:
            signal_name: Name of the signal

        Returns:
            Signal: The requested signal

        Raises:
            ValueError: If signal is not found
        """
        # Convert underscores to hyphens for signal lookup
        signal_key = signal_name.replace("_", "-")

        try:
            return self._namespace[signal_key]
        except KeyError:
            available_signals = list(self._namespace.keys())
            raise ValueError(f"Signal '{signal_name}' not found. Available signals: {available_signals}") from None

    def get_signal_names(self) -> list[str]:
        """
        Get all available signal names.

        Returns:
            list[str]: List of signal names
        """
        return [name.replace("-", "_") for name in self._namespace]

    def get_event_count(self) -> int:
        """
        Get the total number of events emitted.

        Returns:
            int: Total event count
        """
        return self._event_count

    def reset_event_count(self) -> None:
        """Reset the event counter."""
        self._event_count = 0


# Global event dispatcher instance
_event_dispatcher: EventDispatcher | None = None


def get_event_dispatcher() -> EventDispatcher:
    """
    Get the global event dispatcher instance.

    Returns:
        EventDispatcher: The global event dispatcher
    """
    global _event_dispatcher
    if _event_dispatcher is None:
        _event_dispatcher = EventDispatcher()
    return _event_dispatcher


def emit_event(signal_name: str, sender: Any | None = None, **context: Any) -> None:
    """
    Convenience function to emit an event using the global dispatcher.

    Args:
        signal_name: Name of the signal to emit
        sender: Optional sender object
        **context: Event context data
    """
    dispatcher = get_event_dispatcher()
    dispatcher.emit(signal_name, sender=sender, **context)


def emit_login_event(context: LoginEventContext, sender: Any | None = None) -> None:
    """
    Convenience function to emit a user login event.

    Args:
        context: Login event context
        sender: Optional sender object
    """
    dispatcher = get_event_dispatcher()
    dispatcher.emit_typed("user_logged_in", context, sender=sender)


def emit_logout_event(context: LogoutEventContext, sender: Any | None = None) -> None:
    """
    Convenience function to emit a user logout event.

    Args:
        context: Logout event context
        sender: Optional sender object
    """
    dispatcher = get_event_dispatcher()
    dispatcher.emit_typed("user_logged_out", context, sender=sender)


def emit_login_failed_event(context: LoginFailedEventContext, sender: Any | None = None) -> None:
    """
    Convenience function to emit a login failed event.

    Args:
        context: Login failed event context
        sender: Optional sender object
    """
    dispatcher = get_event_dispatcher()
    dispatcher.emit_typed("login_failed", context, sender=sender)


def emit_registration_event(context: RegistrationEventContext, sender: Any | None = None) -> None:
    """
    Convenience function to emit a user registration event.

    Args:
        context: Registration event context
        sender: Optional sender object
    """
    dispatcher = get_event_dispatcher()
    dispatcher.emit_typed("user_registered", context, sender=sender)

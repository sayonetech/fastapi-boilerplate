"""Event system for the Madcrow application.

This module provides a centralized event-driven architecture using Blinker signals.
It enables loose coupling between components by allowing them to communicate through events.

Key components:
- signals: Predefined signal definitions
- dispatcher: Centralized event dispatcher
- handlers: Event handler registry and decorators
- models: Event context models

Usage:
    from events import emit_event, on_event
    from events.signals import user_logged_in

    # Emit an event
    emit_event('user_logged_in', user_id='123', timestamp=datetime.now())

    # Register an event handler
    @on_event('user_logged_in')
    def handle_user_login(sender, **context):
        print(f"User {context['user_id']} logged in")
"""

from .dispatcher import emit_event, get_event_dispatcher
from .event_handlers import register_all_handlers
from .handlers import on_event, register_handler
from .signals import (
    login_failed,
    user_logged_in,
    user_logged_out,
    user_registered,
)

__all__ = [
    "emit_event",
    "get_event_dispatcher",
    "login_failed",
    "on_event",
    "register_all_handlers",
    "register_handler",
    "user_logged_in",
    "user_logged_out",
    "user_registered",
]

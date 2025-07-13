"""Event system extension for FastAPI application.

This extension initializes the event system and registers default event handlers
during application startup.
"""

import logging

from ..beco_app import BecoApp
from ..events import get_event_dispatcher
from ..events.event_handlers import register_all_handlers

logger = logging.getLogger(__name__)


def init_events(app: BecoApp) -> None:
    """
    Initialize the event system for the BecoApp application.

    This function:
    1. Initializes the global event dispatcher
    2. Registers default event handlers
    3. Sets up event system logging

    Args:
        app: FastAPI application instance
    """
    try:
        logger.info("Initializing event system...")

        # Initialize the global event dispatcher
        dispatcher = get_event_dispatcher()

        # Register all event handlers
        register_all_handlers()

        # Store dispatcher in app state for access if needed
        app.state.event_dispatcher = dispatcher

        # Log available signals
        signal_names = dispatcher.get_signal_names()
        logger.info(f"Event system initialized with {len(signal_names)} signals: {', '.join(signal_names)}")

    except Exception as e:
        logger.exception("Failed to initialize event system")
        raise


def get_app_event_dispatcher(app: BecoApp):
    """
    Get the event dispatcher from the FastAPI app state.

    Args:
        app: FastAPI application instance

    Returns:
        EventDispatcher: The application's event dispatcher
    """
    return getattr(app.state, "event_dispatcher", get_event_dispatcher())


def init_app(app: BecoApp) -> None:
    """
    Initialize the event system extension for the FastAPI application.

    This is the main entry point called by the extension system.

    Args:
        app: FastAPI application instance
    """
    init_events(app)

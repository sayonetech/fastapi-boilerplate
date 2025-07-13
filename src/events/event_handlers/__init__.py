"""Event handlers package for the Madcrow application.

This package contains all event handlers organized by category.
Event handlers are functions that respond to specific events in the system.

Structure:
- auth_handlers.py: Authentication-related event handlers
- security_handlers.py: Security monitoring event handlers
- audit_handlers.py: Audit logging event handlers
- system_handlers.py: System event handlers

Usage:
    from events.event_handlers import register_all_handlers

    # Register all handlers during application startup
    register_all_handlers()
"""

from .audit_handlers import (
    log_login_failure,
    log_user_login,
    log_user_logout,
    log_user_registration,
)

# Import specific functions instead of using star imports
from .auth_handlers import (
    cleanup_user_session_data,
    handle_user_login,
    handle_user_logout,
    handle_user_registration,
    update_user_activity_metrics,
)
from .security_handlers import (
    monitor_suspicious_activity,
    track_failed_login_attempts,
)
from .system_handlers import (
    handle_system_shutdown,
    handle_system_startup,
)

__all__ = [
    "cleanup_user_session_data",
    "handle_system_shutdown",
    # System handlers
    "handle_system_startup",
    # Auth handlers
    "handle_user_login",
    "handle_user_logout",
    "handle_user_registration",
    "log_login_failure",
    # Audit handlers
    "log_user_login",
    "log_user_logout",
    "log_user_registration",
    # Security handlers
    "monitor_suspicious_activity",
    # Registration function
    "register_all_handlers",
    "track_failed_login_attempts",
    "update_user_activity_metrics",
]


def register_all_handlers() -> None:
    """
    Register all event handlers from all modules.

    This function should be called during application startup to ensure
    all event handlers are properly registered with the event system.
    """
    # Import all handler modules to trigger decorator registration
    import logging

    logger = logging.getLogger(__name__)
    logger.info("All event handlers registered successfully")

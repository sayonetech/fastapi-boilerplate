"""Audit logging event handlers.

This module contains event handlers that provide audit logging functionality
for tracking user actions and system events for compliance and monitoring.
"""

import logging
from datetime import UTC, datetime
from typing import Any

from ..handlers import (
    on_login_failed,
    on_user_login,
    on_user_logout,
    on_user_registered,
)

logger = logging.getLogger(__name__)


@on_user_login()
def log_user_login(sender: Any, **context: Any) -> None:
    """
    Log user login events for audit purposes.

    This handler creates audit log entries for successful user logins,
    which are essential for security compliance and monitoring.

    Args:
        sender: Event sender
        **context: Login event context
    """
    user_id = context.get("user_id")
    email = context.get("email")
    ip_address = context.get("ip_address", "unknown")
    timestamp = context.get("timestamp", datetime.now(UTC))
    is_admin = context.get("is_admin", False)
    remember_me = context.get("remember_me", False)

    logger.info(
        f"AUDIT: User login - {email} (ID: {user_id}) from {ip_address}",
        extra={
            "event_type": "audit_user_login",
            "audit_category": "authentication",
            "user_id": str(user_id),
            "email": email,
            "ip_address": ip_address,
            "timestamp": timestamp.isoformat() if isinstance(timestamp, datetime) else timestamp,
            "is_admin": is_admin,
            "remember_me": remember_me,
            "action": "login_success",
            "severity": "info",
        },
    )


@on_user_logout()
def log_user_logout(sender: Any, **context: Any) -> None:
    """
    Log user logout events for audit purposes.

    This handler creates audit log entries for user logouts,
    tracking session duration and logout reasons.

    Args:
        sender: Event sender
        **context: Logout event context
    """
    user_id = context.get("user_id")
    email = context.get("email")
    logout_reason = context.get("logout_reason", "unknown")
    session_duration = context.get("session_duration")
    timestamp = context.get("timestamp", datetime.now(UTC))
    ip_address = context.get("ip_address", "unknown")

    logger.info(
        f"AUDIT: User logout - {email} (ID: {user_id}) - {logout_reason}",
        extra={
            "event_type": "audit_user_logout",
            "audit_category": "authentication",
            "user_id": str(user_id),
            "email": email,
            "logout_reason": logout_reason,
            "session_duration": session_duration,
            "timestamp": timestamp.isoformat() if isinstance(timestamp, datetime) else timestamp,
            "ip_address": ip_address,
            "action": "logout",
            "severity": "info",
        },
    )


@on_login_failed()
def log_login_failure(sender: Any, **context: Any) -> None:
    """
    Log failed login attempts for audit and security purposes.

    This handler creates audit log entries for failed login attempts,
    which are crucial for security monitoring and threat detection.

    Args:
        sender: Event sender
        **context: Login failure event context
    """
    email = context.get("email")
    failure_reason = context.get("failure_reason", "unknown")
    ip_address = context.get("ip_address", "unknown")
    attempt_count = context.get("attempt_count")
    timestamp = context.get("timestamp", datetime.now(UTC))
    user_agent = context.get("user_agent")

    # Determine severity based on failure reason and attempt count
    severity = "warning"
    if (
        attempt_count
        and attempt_count >= 3
        or failure_reason in ["account_banned", "account_closed", "suspicious_activity"]
    ):
        severity = "error"

    logger.warning(
        f"AUDIT: Login failed - {email} from {ip_address} - {failure_reason}",
        extra={
            "event_type": "audit_login_failed",
            "audit_category": "security",
            "email": email,
            "failure_reason": failure_reason,
            "ip_address": ip_address,
            "attempt_count": attempt_count,
            "timestamp": timestamp.isoformat() if isinstance(timestamp, datetime) else timestamp,
            "user_agent": user_agent,
            "action": "login_failed",
            "severity": severity,
        },
    )


@on_user_registered()
def log_user_registration(sender: Any, **context: Any) -> None:
    """
    Log user registration events for audit purposes.

    This handler creates audit log entries for new user registrations,
    tracking account creation and initial status.

    Args:
        sender: Event sender
        **context: Registration event context
    """
    user_id = context.get("user_id")
    email = context.get("email")
    name = context.get("name")
    account_status = context.get("account_status")
    ip_address = context.get("ip_address", "unknown")
    timestamp = context.get("timestamp", datetime.now(UTC))

    logger.info(
        f"AUDIT: User registration - {email} (ID: {user_id}, Name: {name}) with status {account_status}",
        extra={
            "event_type": "audit_user_registration",
            "audit_category": "account_management",
            "user_id": str(user_id),
            "email": email,
            "name": name,
            "account_status": account_status,
            "ip_address": ip_address,
            "timestamp": timestamp.isoformat() if isinstance(timestamp, datetime) else timestamp,
            "action": "user_registration",
            "severity": "info",
        },
    )


# Additional audit handlers for other events can be added here
# Examples:

# @on_event('password_changed')
# def log_password_change(sender: Any, **context: Any) -> None:
#     """Log password change events."""
#     pass

# @on_event('account_activated')
# def log_account_activation(sender: Any, **context: Any) -> None:
#     """Log account activation events."""
#     pass

# @on_event('account_banned')
# def log_account_ban(sender: Any, **context: Any) -> None:
#     """Log account ban events."""
#     pass

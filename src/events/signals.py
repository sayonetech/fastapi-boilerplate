"""Signal definitions for the event system.

This module defines all the signals (events) that can be emitted in the application.
Each signal represents a specific event type and can carry context data.

Signals are created using Blinker's Namespace to ensure proper organization
and avoid naming conflicts.
"""

from blinker import Namespace

# Create a namespace for our application signals
madcrow_signals = Namespace()

# Authentication-related signals
user_logged_in = madcrow_signals.signal("user-logged-in")
"""Signal emitted when a user successfully logs in.

Context: LoginEventContext
- user_id: UUID of the logged-in user
- email: User's email address
- name: User's display name
- is_admin: Whether the user is an admin
- remember_me: Whether remember me was selected
- ip_address: Client IP address
- user_agent: User agent string
- timestamp: Login timestamp
"""

user_logged_out = madcrow_signals.signal("user-logged-out")
"""Signal emitted when a user logs out.

Context: LogoutEventContext
- user_id: UUID of the logged-out user
- email: User's email address
- session_duration: Duration of the session in seconds
- logout_reason: Reason for logout (user_initiated, token_expired, etc.)
- ip_address: Client IP address
- timestamp: Logout timestamp
"""

login_failed = madcrow_signals.signal("login-failed")
"""Signal emitted when a login attempt fails.

Context: LoginFailedEventContext
- email: Attempted email address
- failure_reason: Reason for failure (invalid_credentials, account_banned, etc.)
- attempt_count: Number of failed attempts (if tracked)
- ip_address: Client IP address
- user_agent: User agent string
- timestamp: Failure timestamp
"""

user_registered = madcrow_signals.signal("user-registered")
"""Signal emitted when a new user registers.

Context: RegistrationEventContext
- user_id: UUID of the new user
- email: User's email address
- name: User's display name
- account_status: Initial account status
- ip_address: Client IP address
- user_agent: User agent string
- timestamp: Registration timestamp
"""

# Account management signals
account_activated = madcrow_signals.signal("account-activated")
"""Signal emitted when an account is activated.

Context: GenericEventContext with account activation data
"""

account_banned = madcrow_signals.signal("account-banned")
"""Signal emitted when an account is banned.

Context: GenericEventContext with ban details
"""

account_closed = madcrow_signals.signal("account-closed")
"""Signal emitted when an account is closed.

Context: GenericEventContext with closure details
"""

# Security-related signals
password_changed = madcrow_signals.signal("password-changed")
"""Signal emitted when a user changes their password.

Context: GenericEventContext with password change details
"""

suspicious_activity = madcrow_signals.signal("suspicious-activity")
"""Signal emitted when suspicious activity is detected.

Context: GenericEventContext with activity details
"""

# Session management signals
session_expired = madcrow_signals.signal("session-expired")
"""Signal emitted when a user session expires.

Context: GenericEventContext with session details
"""

token_refreshed = madcrow_signals.signal("token-refreshed")
"""Signal emitted when an access token is refreshed.

Context: GenericEventContext with token refresh details
"""

# System signals
system_startup = madcrow_signals.signal("system-startup")
"""Signal emitted when the application starts up.

Context: GenericEventContext with startup details
"""

system_shutdown = madcrow_signals.signal("system-shutdown")
"""Signal emitted when the application shuts down.

Context: GenericEventContext with shutdown details
"""

# Export all signals for easy access
__all__ = [
    "account_activated",
    "account_banned",
    "account_closed",
    "login_failed",
    "madcrow_signals",
    "password_changed",
    "session_expired",
    "suspicious_activity",
    "system_shutdown",
    "system_startup",
    "token_refreshed",
    "user_logged_in",
    "user_logged_out",
    "user_registered",
]

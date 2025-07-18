#!/usr/bin/env python3
"""
Event System Usage Example

This example demonstrates how to use the Madcrow event system
for handling authentication events and creating custom handlers.
"""

import logging
from datetime import UTC, datetime
from uuid import uuid4

# Set up logging to see event handler output
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

import os

# Add the parent directory to the path so we can import src
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import the event system components
from src.events import emit_event, on_event
from src.events.dispatcher import emit_login_event, emit_login_failed_event
from src.events.handlers import on_login_failed, on_user_login, register_handler
from src.events.models import LoginEventContext, LoginFailedEventContext

print("🚀 Madcrow Event System Example")
print("=" * 50)

# Example 1: Using decorators to register event handlers
print("\n📝 Example 1: Decorator-based Event Handlers")


@on_user_login()
def audit_user_login(sender, **context):
    """Audit log for user logins."""
    print(f"🔍 AUDIT: User {context['email']} logged in from {context.get('ip_address', 'unknown')}")


@on_login_failed()
def security_monitor(sender, **context):
    """Monitor failed login attempts for security."""
    attempt_count = context.get("attempt_count", 1)
    if attempt_count >= 3:
        print(f"🚨 SECURITY ALERT: {attempt_count} failed attempts for {context['email']}")
    else:
        print(f"⚠️  Failed login: {context['email']} - {context['failure_reason']}")


@on_event("user_logged_in")
def welcome_message(sender, **context):
    """Send welcome message to users."""
    if context.get("is_admin"):
        print(f"👑 Welcome back, Admin {context['name']}!")
    else:
        print(f"👋 Welcome back, {context['name']}!")


# Example 2: Programmatic handler registration
print("\n📝 Example 2: Programmatic Handler Registration")


def metrics_collector(sender, **context):
    """Collect login metrics."""
    print(f"📊 METRICS: Login recorded for user {context['email']} at {context['timestamp']}")


# Register the handler programmatically
register_handler("user_logged_in", metrics_collector)

# Example 3: Emit events with typed contexts
print("\n📝 Example 3: Emitting Events")

# Successful login event
print("\n--- Simulating successful login ---")
login_context = LoginEventContext(
    user_id=uuid4(),
    email="alice@example.com",
    name="Alice Johnson",
    is_admin=False,
    remember_me=True,
    ip_address="192.168.1.100",
    timestamp=datetime.now(UTC),
)

emit_login_event(login_context)

# Admin login event
print("\n--- Simulating admin login ---")
admin_context = LoginEventContext(
    user_id=uuid4(),
    email="admin@example.com",
    name="System Admin",
    is_admin=True,
    remember_me=False,
    ip_address="192.168.1.10",
    timestamp=datetime.now(UTC),
)

emit_login_event(admin_context)

# Failed login event
print("\n--- Simulating failed login ---")
failed_context = LoginFailedEventContext(
    email="hacker@example.com",
    failure_reason="invalid_credentials",
    ip_address="192.168.1.200",
    attempt_count=3,
    timestamp=datetime.now(UTC),
)

emit_login_failed_event(failed_context)

# Example 4: Using predefined signals
print("\n📝 Example 4: Using Predefined Signals")


@on_event("system_startup")
def handle_system_startup(sender, **context):
    print(f"🎯 System startup event: {context}")


# Emit a system startup event
emit_event("system_startup", version="1.0.0", environment="development")

print("\n" + "=" * 50)
print("✅ Event system example completed successfully!")
print("\nKey takeaways:")
print("• Use @on_event() decorator for simple event handlers")
print("• Use @on_user_login(), @on_login_failed() for auth events")
print("• Use register_handler() for programmatic registration")
print("• Use typed context models for better type safety")
print("• Events are processed synchronously by default")
print("• Multiple handlers can listen to the same event")
print("• Event emission is resilient to handler failures")

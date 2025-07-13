#!/usr/bin/env python3
"""
Custom Event Creation and Handling Example

This example demonstrates how to:
1. Create custom events and signals
2. Define typed event contexts
3. Create event handlers to capture events
4. Emit events from your application code
5. Handle events with different patterns
"""

import logging
import os
import sys
from datetime import UTC, datetime
from uuid import UUID, uuid4

# Add the parent directory to the path so we can import src
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Set up logging
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

# Import event system components
from src.events import emit_event, on_event
from src.events.dispatcher import get_event_dispatcher
from src.events.handlers import register_handler
from src.events.models import BaseEventContext
from src.events.signals import madcrow_signals

print("🎯 Custom Event Creation and Handling Example")
print("=" * 60)

# Step 1: Define a custom signal (normally done in signals.py)
print("\n📝 Step 1: Defining Custom Signals")
user_notification_sent = madcrow_signals.signal("user-notification-sent")
order_completed = madcrow_signals.signal("order-completed")
print("✅ Custom signals defined: user_notification_sent, order_completed")

# Step 2: Define custom event context models (normally done in models.py)
print("\n📝 Step 2: Defining Event Context Models")

from pydantic import Field


class NotificationEventContext(BaseEventContext):
    """Context for notification events."""

    user_id: UUID = Field(..., description="User ID")
    notification_type: str = Field(..., description="Type of notification")
    message: str = Field(..., description="Notification message")
    channel: str = Field(..., description="Delivery channel")
    success: bool = Field(..., description="Whether notification was sent successfully")


class OrderEventContext(BaseEventContext):
    """Context for order events."""

    order_id: str = Field(..., description="Order ID")
    user_id: UUID = Field(..., description="User ID")
    total_amount: float = Field(..., description="Order total amount")
    items_count: int = Field(..., description="Number of items")


print("✅ Event context models defined")

# Step 3: Create event handlers to capture events
print("\n📝 Step 3: Creating Event Handlers")

# Track all events for demonstration
captured_events = []


@on_event("user_notification_sent")
def log_notification_event(sender, **context):
    """Log notification events for audit."""
    captured_events.append(("notification_audit", context))
    user_id = context.get("user_id")
    notification_type = context.get("notification_type")
    channel = context.get("channel")
    success = context.get("success")

    status = "✅ SUCCESS" if success else "❌ FAILED"
    print(f"📧 AUDIT: {status} - {notification_type} notification sent to user {user_id} via {channel}")


@on_event("user_notification_sent")
def track_notification_metrics(sender, **context):
    """Track notification delivery metrics."""
    captured_events.append(("notification_metrics", context))
    notification_type = context.get("notification_type")
    channel = context.get("channel")
    success = context.get("success")

    print(f"📊 METRICS: {notification_type} via {channel} - {'delivered' if success else 'failed'}")


@on_event("user_notification_sent")
def handle_failed_notifications(sender, **context):
    """Handle failed notification deliveries."""
    if not context.get("success"):
        captured_events.append(("notification_failure", context))
        user_id = context.get("user_id")
        notification_type = context.get("notification_type")

        print(f"🚨 ALERT: Failed to send {notification_type} to user {user_id} - triggering retry logic")


@on_event("order_completed")
def process_order_completion(sender, **context):
    """Handle order completion events."""
    captured_events.append(("order_completion", context))
    order_id = context.get("order_id")
    user_id = context.get("user_id")
    total_amount = context.get("total_amount")

    print(f"🛒 ORDER: Order {order_id} completed for user {user_id} - ${total_amount:.2f}")


@on_event("order_completed")
def send_order_confirmation(sender, **context):
    """Send order confirmation notification."""
    captured_events.append(("order_notification", context))
    order_id = context.get("order_id")
    user_id = context.get("user_id")

    print(f"📨 NOTIFICATION: Sending order confirmation for {order_id} to user {user_id}")


# Programmatic handler registration example
def custom_analytics_handler(sender, **context):
    """Custom analytics handler registered programmatically."""
    captured_events.append(("analytics", context))
    print(f"📈 ANALYTICS: Event captured - {len(context)} data points")


register_handler("order_completed", custom_analytics_handler)

print("✅ Event handlers registered")

# Step 4: Simulate emitting events
print("\n📝 Step 4: Emitting Custom Events")

# Example 1: Successful notification
print("\n--- Example 1: Successful Email Notification ---")
notification_context = NotificationEventContext(
    user_id=uuid4(),
    notification_type="welcome",
    message="Welcome to our platform!",
    channel="email",
    success=True,
    timestamp=datetime.now(UTC),
)

# Emit using typed context (recommended)
dispatcher = get_event_dispatcher()
dispatcher.emit_typed("user_notification_sent", notification_context)

# Example 2: Failed SMS notification
print("\n--- Example 2: Failed SMS Notification ---")
failed_notification = NotificationEventContext(
    user_id=uuid4(),
    notification_type="verification",
    message="Your verification code is 123456",
    channel="sms",
    success=False,
    timestamp=datetime.now(UTC),
)

dispatcher.emit_typed("user_notification_sent", failed_notification)

# Example 3: Order completion
print("\n--- Example 3: Order Completion ---")
order_context = OrderEventContext(
    order_id="ORD-12345", user_id=uuid4(), total_amount=99.99, items_count=3, timestamp=datetime.now(UTC)
)

dispatcher.emit_typed("order_completed", order_context)

# Example 4: Simple event emission
print("\n--- Example 4: Simple Event Emission ---")
emit_event("order_completed", order_id="ORD-67890", user_id=str(uuid4()), total_amount=149.99, items_count=5)

# Step 5: Show results
print("\n📝 Step 5: Event Handling Results")
print(f"\n📊 Total events captured: {len(captured_events)}")

event_types = {}
for event_type, context in captured_events:
    event_types[event_type] = event_types.get(event_type, 0) + 1

print("\n📈 Events by handler type:")
for event_type, count in event_types.items():
    print(f"  • {event_type}: {count} events")

print("\n" + "=" * 60)
print("✅ Custom Event Example Completed Successfully!")

print("\n🎯 Key Takeaways:")
print("• Define custom signals in signals.py")
print("• Create typed context models for better validation")
print("• Use @on_event() decorator to capture events")
print("• Multiple handlers can listen to the same event")
print("• Use register_handler() for programmatic registration")
print("• Emit events with emit_event() or dispatcher.emit_typed()")
print("• Event handlers run independently and can't break each other")
print("• Events enable loose coupling between components")

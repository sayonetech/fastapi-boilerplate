# Event System Documentation

The Madcrow backend implements a comprehensive event-driven architecture using Blinker signals to enable loose coupling between components and provide extensibility for future features.

## Overview

The event system allows different parts of the application to communicate through events without direct dependencies. This enables:

- **Audit logging** - Track user actions and system events
- **Security monitoring** - Detect suspicious activities
- **External integrations** - Notify external services of important events
- **Analytics** - Collect user behavior data
- **Modular features** - Add new functionality without modifying existing code

## Architecture

### Core Components

1. **Signals** (`src/events/signals.py`) - Predefined event types
2. **Dispatcher** (`src/events/dispatcher.py`) - Centralized event emission
3. **Handlers** (`src/events/handlers.py`) - Event handler registration system
4. **Models** (`src/events/models.py`) - Typed event context models
5. **Event Handlers Package** (`src/events/event_handlers/`) - Organized event handlers
   - `auth_handlers.py` - Authentication-related handlers
   - `audit_handlers.py` - Audit logging handlers
   - `security_handlers.py` - Security monitoring handlers
   - `system_handlers.py` - System event handlers

### Event Flow

```
[Event Source] → [Dispatcher] → [Signal] → [Registered Handlers]
     ↓              ↓             ↓              ↓
Auth Service → emit_event() → user_logged_in → [Audit Logger, Metrics, etc.]
```

## Available Events

### Authentication Events

#### `user_logged_in`

Emitted when a user successfully logs in.

**Context:** `LoginEventContext`

- `user_id`: User account ID
- `email`: User email address
- `name`: User display name
- `is_admin`: Whether user is admin
- `remember_me`: Whether remember me was selected
- `ip_address`: Client IP address
- `timestamp`: Login timestamp
- `session_duration`: Session duration in seconds

#### `user_logged_out`

Emitted when a user logs out.

**Context:** `LogoutEventContext`

- `user_id`: User account ID
- `email`: User email address
- `session_duration`: Session duration in seconds
- `logout_reason`: Reason for logout
- `ip_address`: Client IP address
- `timestamp`: Logout timestamp

#### `login_failed`

Emitted when a login attempt fails.

**Context:** `LoginFailedEventContext`

- `email`: Attempted email address
- `failure_reason`: Reason for failure
- `attempt_count`: Number of failed attempts
- `ip_address`: Client IP address
- `timestamp`: Failure timestamp

#### `user_registered`

Emitted when a new user registers.

**Context:** `RegistrationEventContext`

- `user_id`: New user account ID
- `email`: User email address
- `name`: User display name
- `account_status`: Initial account status
- `ip_address`: Client IP address
- `timestamp`: Registration timestamp

### Account Management Events

- `account_activated` - Account activation
- `account_banned` - Account ban
- `account_closed` - Account closure
- `password_changed` - Password change

### Security Events

- `suspicious_activity` - Suspicious activity detection
- `session_expired` - Session expiration
- `token_refreshed` - Token refresh

### System Events

- `system_startup` - Application startup
- `system_shutdown` - Application shutdown

## Usage

### Emitting Events

#### Using the Dispatcher

```python
from events import emit_event

# Emit a simple event
emit_event('user_logged_in', user_id='123', email='user@example.com')

# Emit with typed context
from events.models import LoginEventContext
from events.dispatcher import emit_login_event

context = LoginEventContext(
    user_id=user.id,
    email=user.email,
    name=user.name,
    ip_address=request_ip
)
emit_login_event(context)
```

#### In Services

```python
class AuthService:
    def authenticate_user(self, email: str, password: str) -> TokenPair:
        # ... authentication logic ...

        # Emit login success event
        self._emit_login_success_event(
            user=user,
            ip_address=login_ip,
            timestamp=datetime.now(UTC)
        )

        return token_pair
```

### Capturing/Handling Events

There are several ways to capture and handle events in the system:

#### Method 1: Using Decorators (Recommended)

The most common and clean way to handle events:

```python
from events.handlers import on_event, on_user_login, on_login_failed

# Handle specific authentication events
@on_user_login()
def handle_user_login(sender, **context):
    user_id = context['user_id']
    email = context['email']
    print(f"User {email} logged in")

@on_login_failed()
def handle_login_failure(sender, **context):
    email = context['email']
    reason = context['failure_reason']
    print(f"Login failed for {email}: {reason}")

# Handle any event by name
@on_event('custom_event')
def handle_custom_event(sender, **context):
    print(f"Custom event received: {context}")

# Handle system events
@on_event('system_startup')
def handle_startup(sender, **context):
    version = context.get('version', 'unknown')
    print(f"System started - version {version}")
```

#### Method 2: Programmatic Registration

For dynamic handler registration or when decorators aren't suitable:

```python
from events.handlers import register_handler

def my_handler(sender, **context):
    # Handle the event
    print(f"Event received: {context}")

# Register the handler
register_handler('user_logged_in', my_handler)

# You can also register multiple handlers for the same event
def another_handler(sender, **context):
    # Different handling logic
    pass

register_handler('user_logged_in', another_handler)
```

#### Method 3: Conditional Event Handling

Handle events based on specific conditions:

```python
@on_user_login()
def handle_admin_login(sender, **context):
    """Only handle admin logins."""
    if context.get('is_admin'):
        print(f"Admin {context['email']} logged in")
        # Special admin login logic

@on_login_failed()
def handle_brute_force(sender, **context):
    """Handle potential brute force attacks."""
    attempt_count = context.get('attempt_count', 0)
    if attempt_count >= 5:
        ip_address = context.get('ip_address')
        print(f"Potential brute force from {ip_address}")
        # Trigger security measures
```

#### Method 4: Multiple Event Handler

Handle multiple related events in one handler:

```python
# Register the same handler for multiple events
@on_event('user_logged_in')
@on_event('user_logged_out')
def track_user_activity(sender, **context):
    """Track all user activity events."""
    event_type = "login" if 'user_logged_in' in str(sender) else "logout"
    user_id = context.get('user_id')
    print(f"User activity: {event_type} for user {user_id}")
```

#### Method 5: Handler with Error Handling

Robust event handlers with proper error handling:

```python
import logging

logger = logging.getLogger(__name__)

@on_user_login()
def robust_login_handler(sender, **context):
    """Login handler with error handling."""
    try:
        user_id = context.get('user_id')
        email = context.get('email')

        # Your business logic here
        result = process_user_login(user_id, email)

        logger.info(f"Successfully processed login for {email}")
        return result

    except Exception as e:
        logger.exception(f"Error processing login event: {e}")
        # Don't re-raise - let other handlers continue
```

#### Method 6: Async Event Handlers (Advanced)

For handlers that need to perform async operations:

```python
import asyncio
from events.handlers import on_user_login

@on_user_login()
def async_login_handler(sender, **context):
    """Handler that triggers async operations."""
    user_id = context.get('user_id')

    # Run async operation in background
    asyncio.create_task(send_welcome_email(user_id))

async def send_welcome_email(user_id):
    """Async function to send welcome email."""
    # Async email sending logic
    pass
```

### Creating Custom Event Handlers

#### 1. Choose the Right Handler Module

Organize your handlers by category:

- **Authentication logic** → `auth_handlers.py`
- **Audit/compliance logging** → `audit_handlers.py`
- **Security monitoring** → `security_handlers.py`
- **System operations** → `system_handlers.py`

#### 2. Create Handler Function

```python
# In src/events/event_handlers/auth_handlers.py
from ..handlers import on_user_login

@on_user_login()
def my_custom_login_handler(sender, **context):
    user_id = context.get('user_id')
    # Your custom logic here
    print(f"Custom login logic for user {user_id}")
```

#### 3. Handler Registration

Handlers are automatically registered when the module is imported during application startup via `register_all_handlers()`.

### Creating Custom Events

#### 1. Define the Signal

```python
# In src/events/signals.py
custom_event = madcrow_signals.signal('custom-event')
```

#### 2. Create Context Model (Optional)

```python
# In src/events/models.py
class CustomEventContext(BaseEventContext):
    custom_field: str = Field(..., description="Custom field")
```

#### 3. Create Event Handler

```python
# In src/events/event_handlers/your_handlers.py
from ..handlers import on_event

@on_event('custom_event')
def handle_custom_event(sender, **context):
    """Handle custom event."""
    custom_field = context.get('custom_field')
    print(f"Received custom event: {custom_field}")

    # Your custom logic here
    # - Process the event data
    # - Update databases
    # - Send notifications
    # - Trigger other actions
```

#### 4. Register Handler (if in new module)

If you create a new handler module, make sure to import it in the event handlers package:

```python
# In src/events/event_handlers/__init__.py
from . import your_handlers  # noqa: F401

def register_all_handlers() -> None:
    # Import all handler modules to trigger decorator registration
    from . import auth_handlers  # noqa: F401
    from . import audit_handlers  # noqa: F401
    from . import security_handlers  # noqa: F401
    from . import system_handlers  # noqa: F401
    from . import your_handlers  # noqa: F401  # Add your new module
```

#### 5. Emit the Event

```python
from events import emit_event

# Simple emission
emit_event('custom_event', custom_field='value')

# With typed context (recommended)
from events.models import GenericEventContext
from events.dispatcher import get_event_dispatcher

context = GenericEventContext(
    event_type='custom_event',
    data={'custom_field': 'value', 'additional_data': 123}
)

dispatcher = get_event_dispatcher()
dispatcher.emit_typed('custom_event', context)
```

### Complete Example: User Notification System

Here's a complete example showing how to create a custom event for user notifications:

#### 1. Define the Signal and Context

```python
# In src/events/signals.py
user_notification_sent = madcrow_signals.signal('user-notification-sent')

# In src/events/models.py
class NotificationEventContext(BaseEventContext):
    user_id: UUID = Field(..., description="User ID")
    notification_type: str = Field(..., description="Type of notification")
    message: str = Field(..., description="Notification message")
    channel: str = Field(..., description="Delivery channel (email, sms, push)")
    success: bool = Field(..., description="Whether notification was sent successfully")
```

#### 2. Create Event Handlers

```python
# In src/events/event_handlers/notification_handlers.py
from ..handlers import on_event
import logging

logger = logging.getLogger(__name__)

@on_event('user_notification_sent')
def log_notification(sender, **context):
    """Log all notification events for audit."""
    user_id = context.get('user_id')
    notification_type = context.get('notification_type')
    channel = context.get('channel')
    success = context.get('success')

    status = "SUCCESS" if success else "FAILED"
    logger.info(f"NOTIFICATION {status}: {notification_type} sent to user {user_id} via {channel}")

@on_event('user_notification_sent')
def track_notification_metrics(sender, **context):
    """Track notification delivery metrics."""
    notification_type = context.get('notification_type')
    channel = context.get('channel')
    success = context.get('success')

    # Update metrics (pseudo-code)
    # metrics.increment(f'notifications.{notification_type}.{channel}.{"success" if success else "failure"}')

@on_event('user_notification_sent')
def handle_failed_notifications(sender, **context):
    """Handle failed notification deliveries."""
    if not context.get('success'):
        user_id = context.get('user_id')
        notification_type = context.get('notification_type')

        logger.warning(f"Failed to send {notification_type} to user {user_id}")
        # Could trigger retry logic, alternative delivery methods, etc.
```

#### 3. Register Handlers

```python
# In src/events/event_handlers/__init__.py
from . import notification_handlers  # noqa: F401

def register_all_handlers() -> None:
    from . import auth_handlers  # noqa: F401
    from . import audit_handlers  # noqa: F401
    from . import security_handlers  # noqa: F401
    from . import system_handlers  # noqa: F401
    from . import notification_handlers  # noqa: F401  # Add new handlers
```

#### 4. Emit Events from Your Service

```python
# In your notification service
from events.models import NotificationEventContext
from events.dispatcher import get_event_dispatcher

class NotificationService:
    def send_notification(self, user_id: UUID, message: str, channel: str = "email"):
        try:
            # Send notification logic here
            success = self._send_via_channel(user_id, message, channel)

            # Emit event regardless of success/failure
            context = NotificationEventContext(
                user_id=user_id,
                notification_type="general",
                message=message,
                channel=channel,
                success=success
            )

            dispatcher = get_event_dispatcher()
            dispatcher.emit_typed('user_notification_sent', context)

            return success

        except Exception as e:
            # Emit failure event
            context = NotificationEventContext(
                user_id=user_id,
                notification_type="general",
                message=message,
                channel=channel,
                success=False
            )

            dispatcher = get_event_dispatcher()
            dispatcher.emit_typed('user_notification_sent', context)

            raise
```

#### 5. Usage

```python
# In your application code
notification_service = NotificationService()

# This will trigger all the registered handlers
notification_service.send_notification(
    user_id=user.id,
    message="Welcome to our platform!",
    channel="email"
)

# The event system will automatically:
# - Log the notification attempt
# - Update metrics
# - Handle any failures
# - All without the notification service knowing about these concerns
```

## Event Handlers Package

The system includes organized event handlers in the `src/events/event_handlers/` package:

### Authentication Handlers (`auth_handlers.py`)

- `handle_user_login` - Business logic for user logins
- `handle_user_logout` - Business logic for user logouts
- `handle_user_registration` - Business logic for user registration
- `update_user_activity_metrics` - Updates user activity counters
- `cleanup_user_session_data` - Cleans up session data on logout

### Audit Handlers (`audit_handlers.py`)

- `log_user_login` - Logs successful logins
- `log_user_logout` - Logs user logouts
- `log_login_failure` - Logs failed login attempts
- `log_user_registration` - Logs new registrations

### Security Handlers (`security_handlers.py`)

- `monitor_suspicious_activity` - Detects suspicious login patterns
- `track_failed_login_attempts` - Tracks failed login analytics
- `handle_suspicious_activity_alert` - Responds to security alerts
- `handle_session_expiration` - Handles session expiration events

### System Handlers (`system_handlers.py`)

- `handle_system_startup` - System startup logic
- `handle_system_shutdown` - System shutdown logic
- `initialize_system_monitoring` - Monitoring initialization
- `cleanup_system_resources` - Resource cleanup

## Best Practices

### Event Handler Guidelines

1. **Keep handlers lightweight** - Avoid heavy processing in event handlers
2. **Handle exceptions** - Don't let handler failures break the main flow
3. **Use async handlers carefully** - Most handlers should be synchronous
4. **Log appropriately** - Use structured logging for audit trails

### Event Emission Guidelines

1. **Emit events after success** - Only emit events after operations complete successfully
2. **Include relevant context** - Provide enough information for handlers
3. **Use typed contexts** - Prefer typed context models over raw dictionaries
4. **Don't rely on handlers** - The main flow should work even if handlers fail

### Performance Considerations

1. **Weak references** - Use weak references for handlers to prevent memory leaks
2. **Selective handlers** - Only register handlers that are actually needed
3. **Batch operations** - Consider batching for high-frequency events
4. **Async processing** - Move heavy processing to background tasks

## Configuration

Event system configuration is handled through the extension system:

```python
# In src/extensions/ext_events.py
def init_events(app: FastAPI) -> None:
    # Initialize event dispatcher
    dispatcher = get_event_dispatcher()

    # Register default handlers
    register_default_handlers()

    # Store in app state
    app.state.event_dispatcher = dispatcher
```

## Testing

### Testing Event Emission

```python
from events import get_event_dispatcher

def test_login_emits_event():
    dispatcher = get_event_dispatcher()
    events_received = []

    @on_user_login()
    def capture_event(sender, **context):
        events_received.append(context)

    # Perform login
    auth_service.authenticate_user(email, password)

    # Verify event was emitted
    assert len(events_received) == 1
    assert events_received[0]['email'] == email
```

### Testing Event Handlers

```python
def test_login_handler():
    context = {
        'user_id': '123',
        'email': 'test@example.com',
        'timestamp': datetime.now()
    }

    # Call handler directly
    log_user_login(sender=None, **context)

    # Verify expected behavior
    # (check logs, database updates, etc.)
```

## Troubleshooting

### Common Issues

1. **Events not firing** - Check if handlers are registered before events are emitted
2. **Handler exceptions** - Check logs for handler failures
3. **Memory leaks** - Ensure weak references are used for handlers
4. **Performance issues** - Profile handler execution times

### Debugging

Enable debug logging to see event flow:

```python
import logging
logging.getLogger('src.events').setLevel(logging.DEBUG)
```

This will log:

- Event emissions
- Handler registrations
- Handler execution
- Error details

## Quick Reference

### Event Handling Patterns

| Pattern                   | Use Case                     | Example                     |
| ------------------------- | ---------------------------- | --------------------------- |
| `@on_event('event_name')` | Handle any event by name     | `@on_event('custom_event')` |
| `@on_user_login()`        | Handle user login events     | Authentication logic        |
| `@on_login_failed()`      | Handle failed login attempts | Security monitoring         |
| `@on_user_registered()`   | Handle user registration     | Welcome workflows           |
| `register_handler()`      | Programmatic registration    | Dynamic handlers            |

### Event Emission Patterns

| Pattern                      | Use Case                    | Example             |
| ---------------------------- | --------------------------- | ------------------- |
| `emit_event('name', **data)` | Simple event emission       | Quick notifications |
| `emit_login_event(context)`  | Typed authentication events | Login/logout        |
| `dispatcher.emit_typed()`    | Typed custom events         | Complex data        |
| `signal.send()`              | Direct signal emission      | Advanced use cases  |

### Handler Organization

| Module                 | Purpose              | Events                      |
| ---------------------- | -------------------- | --------------------------- |
| `auth_handlers.py`     | Authentication logic | Login, logout, registration |
| `audit_handlers.py`    | Compliance logging   | All user actions            |
| `security_handlers.py` | Security monitoring  | Failed logins, threats      |
| `system_handlers.py`   | System operations    | Startup, shutdown           |

### Best Practices Checklist

- ✅ Use typed context models for complex events
- ✅ Organize handlers by functional area
- ✅ Handle exceptions in event handlers
- ✅ Use descriptive handler function names
- ✅ Log important events for audit trails
- ✅ Keep handlers lightweight and fast
- ✅ Test event handlers independently
- ✅ Document custom events and their contexts

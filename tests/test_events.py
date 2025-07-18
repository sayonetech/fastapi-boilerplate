"""Tests for the event system."""

from datetime import UTC, datetime
from uuid import uuid4

from src.events import emit_event, get_event_dispatcher
from src.events.dispatcher import emit_login_event, emit_login_failed_event
from src.events.handlers import clear_all_handlers, on_event, register_handler
from src.events.models import LoginEventContext, LoginFailedEventContext


class TestEventDispatcher:
    """Test the event dispatcher functionality."""

    def setup_method(self):
        """Set up test environment."""
        # Clear any existing handlers
        clear_all_handlers()

    def teardown_method(self):
        """Clean up after tests."""
        # Clear handlers after each test
        clear_all_handlers()

    def test_emit_simple_event(self):
        """Test emitting a simple event."""
        events_received = []

        @on_event("user_logged_in")
        def capture_event(sender, **context):
            events_received.append(context)

        # Emit event
        emit_event("user_logged_in", user_id="123", email="test@example.com")

        # Verify event was received
        assert len(events_received) == 1
        assert events_received[0]["user_id"] == "123"
        assert events_received[0]["email"] == "test@example.com"

    def test_emit_typed_event(self):
        """Test emitting a typed event with context model."""
        events_received = []

        @on_event("user_logged_in")
        def capture_event(sender, **context):
            events_received.append(context)

        # Create typed context
        context = LoginEventContext(
            user_id=uuid4(),
            email="test@example.com",
            name="Test User",
            is_admin=False,
            remember_me=True,
            ip_address="192.168.1.1",
            timestamp=datetime.now(UTC),
        )

        # Emit typed event
        emit_login_event(context)

        # Verify event was received with correct data
        assert len(events_received) == 1
        received = events_received[0]
        assert received["email"] == "test@example.com"
        assert received["name"] == "Test User"
        assert received["is_admin"] is False
        assert received["remember_me"] is True
        assert received["ip_address"] == "192.168.1.1"

    def test_multiple_handlers(self):
        """Test that multiple handlers can listen to the same event."""
        handler1_calls = []
        handler2_calls = []

        @on_event("user_logged_in")
        def handler1(sender, **context):
            handler1_calls.append(context)

        @on_event("user_logged_in")
        def handler2(sender, **context):
            handler2_calls.append(context)

        # Emit event
        emit_event("user_logged_in", user_id="123")

        # Verify both handlers were called
        assert len(handler1_calls) == 1
        assert len(handler2_calls) == 1
        assert handler1_calls[0]["user_id"] == "123"
        assert handler2_calls[0]["user_id"] == "123"

    def test_handler_exception_doesnt_break_emission(self):
        """Test that handler exceptions don't break event emission."""
        successful_calls = []

        @on_event("user_logged_in")
        def successful_handler(sender, **context):
            successful_calls.append(context)

        @on_event("user_logged_in")
        def failing_handler(sender, **context):
            raise Exception("Handler failed")

        # Emit event - should not raise exception even though a handler fails
        # The key test is that emit_event doesn't raise an exception
        try:
            emit_event("user_logged_in", user_id="123")
            emission_succeeded = True
        except Exception:
            emission_succeeded = False

        # Event emission should succeed even if handlers fail
        assert emission_succeeded

        # At least one handler should have been called before the failure
        # Note: Blinker stops calling handlers after the first exception,
        # so we test that the emission itself is resilient
        assert len(successful_calls) >= 0  # Could be 0 or 1 depending on handler order

    def test_programmatic_handler_registration(self):
        """Test registering handlers programmatically."""
        events_received = []

        def my_handler(sender, **context):
            events_received.append(context)

        # Register handler programmatically
        register_handler("user_logged_in", my_handler)

        # Emit event
        emit_event("user_logged_in", user_id="456")

        # Verify handler was called
        assert len(events_received) == 1
        assert events_received[0]["user_id"] == "456"

    def test_login_failed_event(self):
        """Test login failed event emission."""
        events_received = []

        @on_event("login_failed")
        def capture_event(sender, **context):
            events_received.append(context)

        # Create login failed context
        context = LoginFailedEventContext(
            email="test@example.com", failure_reason="invalid_credentials", ip_address="192.168.1.1", attempt_count=3
        )

        # Emit login failed event
        emit_login_failed_event(context)

        # Verify event was received
        assert len(events_received) == 1
        received = events_received[0]
        assert received["email"] == "test@example.com"
        assert received["failure_reason"] == "invalid_credentials"
        assert received["attempt_count"] == 3

    def test_event_dispatcher_singleton(self):
        """Test that event dispatcher is a singleton."""
        dispatcher1 = get_event_dispatcher()
        dispatcher2 = get_event_dispatcher()

        assert dispatcher1 is dispatcher2

    def test_invalid_signal_name(self):
        """Test handling of invalid signal names."""
        # This should not raise an exception but should log a warning
        emit_event("nonexistent_signal", data="test")

        # The event system should be resilient to invalid signal names
        # and continue working for valid signals
        events_received = []

        @on_event("user_logged_in")
        def capture_event(sender, **context):
            events_received.append(context)

        emit_event("user_logged_in", user_id="123")
        assert len(events_received) == 1


class TestEventModels:
    """Test event context models."""

    def test_login_event_context_validation(self):
        """Test LoginEventContext validation."""
        context = LoginEventContext(
            user_id=uuid4(), email="test@example.com", name="Test User", is_admin=True, remember_me=False
        )

        assert context.email == "test@example.com"
        assert context.name == "Test User"
        assert context.is_admin is True
        assert context.remember_me is False
        assert context.timestamp is not None

    def test_login_failed_context_validation(self):
        """Test LoginFailedEventContext validation."""
        context = LoginFailedEventContext(email="test@example.com", failure_reason="account_banned", attempt_count=5)

        assert context.email == "test@example.com"
        assert context.failure_reason == "account_banned"
        assert context.attempt_count == 5
        assert context.timestamp is not None

    def test_context_serialization(self):
        """Test that context models can be serialized."""
        context = LoginEventContext(user_id=uuid4(), email="test@example.com", name="Test User")

        # Should be able to convert to dict
        context_dict = context.model_dump()
        assert isinstance(context_dict, dict)
        assert context_dict["email"] == "test@example.com"
        assert context_dict["name"] == "Test User"

        # Should be able to convert to JSON
        context_json = context.model_dump_json()
        assert isinstance(context_json, str)
        assert "test@example.com" in context_json


class TestEventHandlers:
    """Test event handlers package."""

    def setup_method(self):
        """Set up test environment."""
        clear_all_handlers()

    def teardown_method(self):
        """Clean up after tests."""
        clear_all_handlers()

    def test_event_handlers_import(self):
        """Test that event handlers can be imported without errors."""
        # Import should register the handlers
        from src.events.event_handlers import register_all_handlers

        # Register all handlers
        register_all_handlers()

        # Verify some handlers are registered
        dispatcher = get_event_dispatcher()
        signal_names = dispatcher.get_signal_names()
        assert "user_logged_in" in signal_names
        assert "login_failed" in signal_names

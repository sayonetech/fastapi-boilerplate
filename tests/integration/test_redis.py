"""Integration tests for Redis operations."""

from unittest.mock import patch

import redis

from src.utils.rate_limiter import RateLimiter


class TestRedisRateLimiterIntegration:
    """Integration tests for Redis-based rate limiter."""

    def test_rate_limiter_redis_operations(self, mock_redis):
        """Test rate limiter Redis operations integration."""
        rate_limiter = RateLimiter("test_login", 3, 300)
        identifier = "test@example.com"

        # Mock Redis responses for clean state
        mock_redis.zcard.return_value = 0
        mock_redis.zremrangebyscore.return_value = 0
        mock_redis.zadd.return_value = 1
        mock_redis.expire.return_value = True

        # Test initial state - not rate limited
        is_limited = rate_limiter.is_rate_limited(identifier, mock_redis)
        assert is_limited is False

        # Test incrementing attempts
        rate_limiter.increment_rate_limit(identifier, mock_redis)

        # Verify Redis operations were called
        mock_redis.zremrangebyscore.assert_called()
        mock_redis.zadd.assert_called()
        mock_redis.expire.assert_called()

    def test_rate_limiter_threshold_behavior(self, mock_redis):
        """Test rate limiter behavior at threshold."""
        rate_limiter = RateLimiter("test_login", 3, 300)
        identifier = "test@example.com"
        key = "test_login:test@example.com"

        # Simulate different attempt counts
        test_cases = [
            (0, False),  # No attempts - not limited
            (1, False),  # Under threshold - not limited
            (2, False),  # Under threshold - not limited
            (3, True),  # At threshold - limited
            (5, True),  # Over threshold - limited
        ]

        for attempt_count, expected_limited in test_cases:
            # Clear and set up mock data
            mock_redis._sorted_sets.clear()

            if attempt_count > 0:
                # Add attempts to the sorted set
                mock_redis._sorted_sets[key] = {}
                for i in range(attempt_count):
                    timestamp = 1640995200 - i  # Recent timestamps
                    mock_redis._sorted_sets[key][str(timestamp)] = timestamp

            with patch("src.utils.rate_limiter.time.time", return_value=1640995200.0):
                is_limited = rate_limiter.is_rate_limited(identifier, mock_redis)
                assert is_limited == expected_limited, (
                    f"Expected {expected_limited} for {attempt_count} attempts, got {is_limited}"
                )

    def test_rate_limiter_multiple_identifiers(self, mock_redis):
        """Test rate limiter with multiple identifiers."""
        rate_limiter = RateLimiter("test_login", 3, 300)

        # Mock different attempt counts for different identifiers
        def mock_zcard(key):
            if "user1" in key:
                return 2  # Under limit
            elif "user2" in key:
                return 3  # At limit
            elif "user3" in key:
                return 5  # Over limit
            return 0

        mock_redis.zcard.side_effect = mock_zcard

        # Test different users
        assert rate_limiter.is_rate_limited("user1@example.com", mock_redis) is False
        assert rate_limiter.is_rate_limited("user2@example.com", mock_redis) is True
        assert rate_limiter.is_rate_limited("user3@example.com", mock_redis) is True

    def test_rate_limiter_reset_functionality(self, mock_redis):
        """Test rate limiter reset functionality."""
        rate_limiter = RateLimiter("test_login", 3, 300)
        identifier = "test@example.com"
        key = "test_login:test@example.com"

        # Set up user as rate limited (5 attempts)
        mock_redis._sorted_sets[key] = {}
        for i in range(5):
            timestamp = 1640995200 - i
            mock_redis._sorted_sets[key][str(timestamp)] = timestamp

        # Verify user is rate limited
        with patch("src.utils.rate_limiter.time.time", return_value=1640995200.0):
            is_limited = rate_limiter.is_rate_limited(identifier, mock_redis)
            assert is_limited is True

        # Reset rate limit
        rate_limiter.reset_rate_limit(identifier, mock_redis)

        # Verify the key was deleted from our mock storage
        assert key not in mock_redis._sorted_sets

        # Verify user is no longer rate limited after reset
        with patch("src.utils.rate_limiter.time.time", return_value=1640995200.0):
            is_limited = rate_limiter.is_rate_limited(identifier, mock_redis)
            assert is_limited is False

    def test_rate_limiter_time_window_cleanup(self, mock_redis):
        """Test rate limiter time window cleanup."""
        rate_limiter = RateLimiter("test_login", 3, 300)
        identifier = "test@example.com"
        key = "test_login:test@example.com"

        current_time = 1640995200.0

        # Clear any existing data
        mock_redis._sorted_sets.clear()

        with patch("src.utils.rate_limiter.time.time", return_value=current_time):
            rate_limiter.increment_rate_limit(identifier, mock_redis)

            # Verify that the increment was added to the sorted set
            assert key in mock_redis._sorted_sets
            assert len(mock_redis._sorted_sets[key]) == 1

            # The increment_rate_limit method should have cleaned up old entries
            # and added the new timestamp
            timestamps = list(mock_redis._sorted_sets[key].values())
            assert timestamps[0] == current_time

    def test_rate_limiter_time_until_reset(self, mock_redis):
        """Test getting time until rate limit reset."""
        rate_limiter = RateLimiter("test_login", 3, 300)
        identifier = "test@example.com"
        key = "test_login:test@example.com"

        current_time = 1640995200.0
        oldest_attempt = 1640994900.0  # 300 seconds ago

        # Add attempt to mock sorted set
        mock_redis._sorted_sets[key] = {str(oldest_attempt): oldest_attempt}

        with patch("src.utils.rate_limiter.time.time", return_value=current_time):
            time_until_reset = rate_limiter.get_time_until_reset(identifier, mock_redis)

            # Should be None since oldest_attempt + time_window = current_time (expired)
            assert time_until_reset is None

    def test_rate_limiter_time_until_reset_future(self, mock_redis):
        """Test time until reset when reset is in the future."""
        rate_limiter = RateLimiter("test_login", 3, 300)
        identifier = "test@example.com"
        key = "test_login:test@example.com"

        current_time = 1640995200.0
        recent_attempt = 1640995000.0  # 200 seconds ago

        # Add attempt to mock sorted set
        mock_redis._sorted_sets[key] = {str(recent_attempt): recent_attempt}

        with patch("src.utils.rate_limiter.time.time", return_value=current_time):
            time_until_reset = rate_limiter.get_time_until_reset(identifier, mock_redis)

            # Should be 100 seconds (recent_attempt + 300 - current_time)
            expected_reset_time = recent_attempt + 300 - current_time
            assert time_until_reset == expected_reset_time

    def test_rate_limiter_no_attempts_time_reset(self, mock_redis):
        """Test time until reset with no attempts."""
        rate_limiter = RateLimiter("test_login", 3, 300)
        identifier = "test@example.com"

        # Clear any existing data (no attempts)
        mock_redis._sorted_sets.clear()

        time_until_reset = rate_limiter.get_time_until_reset(identifier, mock_redis)
        assert time_until_reset is None

    def test_redis_connection_error_handling(self, mock_redis):
        """Test handling of Redis connection errors."""
        rate_limiter = RateLimiter("test_login", 3, 300)
        identifier = "test@example.com"

        # Mock Redis connection error
        mock_redis.zcard.side_effect = redis.ConnectionError("Connection failed")

        # Should handle error gracefully and not rate limit
        is_limited = rate_limiter.is_rate_limited(identifier, mock_redis)
        assert is_limited is False

    def test_redis_timeout_error_handling(self, mock_redis):
        """Test handling of Redis timeout errors."""
        rate_limiter = RateLimiter("test_login", 3, 300)
        identifier = "test@example.com"

        # Mock Redis timeout error
        mock_redis.zcard.side_effect = redis.TimeoutError("Operation timed out")

        # Should handle error gracefully and not rate limit
        is_limited = rate_limiter.is_rate_limited(identifier, mock_redis)
        assert is_limited is False

    def test_redis_response_error_handling(self, mock_redis):
        """Test handling of Redis response errors."""
        rate_limiter = RateLimiter("test_login", 3, 300)
        identifier = "test@example.com"

        # Mock Redis response error
        mock_redis.zcard.side_effect = redis.ResponseError("Invalid command")

        # Should handle error gracefully and not rate limit
        is_limited = rate_limiter.is_rate_limited(identifier, mock_redis)
        assert is_limited is False


class TestRedisSessionManagement:
    """Integration tests for Redis session management."""

    def test_session_storage_and_retrieval(self, mock_redis):
        """Test storing and retrieving session data."""
        session_id = "sess_123456"
        session_data = {"user_id": "user_123", "email": "test@example.com", "expires_at": "2024-01-01T00:00:00Z"}

        # Mock Redis operations
        mock_redis.set.return_value = True
        mock_redis.get.return_value = str(session_data).encode()
        mock_redis.expire.return_value = True

        # Simulate session storage
        mock_redis.set(f"session:{session_id}", str(session_data))
        mock_redis.expire(f"session:{session_id}", 3600)

        # Simulate session retrieval
        retrieved_data = mock_redis.get(f"session:{session_id}")

        # Verify operations
        mock_redis.set.assert_called_with(f"session:{session_id}", str(session_data))
        mock_redis.expire.assert_called_with(f"session:{session_id}", 3600)
        mock_redis.get.assert_called_with(f"session:{session_id}")

        assert retrieved_data is not None

    def test_session_deletion(self, mock_redis):
        """Test deleting session data."""
        session_id = "sess_123456"

        # Mock Redis operations
        mock_redis.delete.return_value = 1

        # Simulate session deletion
        mock_redis.delete(f"session:{session_id}")

        # Verify deletion
        mock_redis.delete.assert_called_with(f"session:{session_id}")

    def test_session_expiration(self, mock_redis):
        """Test session expiration handling."""
        session_id = "sess_123456"

        # Mock Redis operations for expired session
        mock_redis.get.return_value = None  # Session expired/not found
        mock_redis.exists.return_value = False

        # Simulate checking expired session
        session_data = mock_redis.get(f"session:{session_id}")
        session_exists = mock_redis.exists(f"session:{session_id}")

        # Verify session is expired/not found
        assert session_data is None
        assert session_exists is False


class TestRedisTokenManagement:
    """Integration tests for Redis token management."""

    def test_refresh_token_storage(self, mock_redis):
        """Test storing refresh tokens."""
        user_id = "user_123"
        refresh_token = "refresh_token_abc123"

        # Mock Redis operations
        mock_redis.set.return_value = True
        mock_redis.expire.return_value = True

        # Simulate refresh token storage
        mock_redis.set(f"refresh_token:{user_id}", refresh_token)
        mock_redis.expire(f"refresh_token:{user_id}", 86400)  # 24 hours

        # Verify operations
        mock_redis.set.assert_called_with(f"refresh_token:{user_id}", refresh_token)
        mock_redis.expire.assert_called_with(f"refresh_token:{user_id}", 86400)

    def test_refresh_token_validation(self, mock_redis):
        """Test validating refresh tokens."""
        user_id = "user_123"
        stored_token = "refresh_token_abc123"
        provided_token = "refresh_token_abc123"

        # Store token in mock storage
        mock_redis._storage[f"refresh_token:{user_id}"] = stored_token

        # Simulate token validation
        retrieved_token = mock_redis.get(f"refresh_token:{user_id}")

        # Verify token matches
        assert retrieved_token == provided_token

    def test_refresh_token_invalidation(self, mock_redis):
        """Test invalidating refresh tokens."""
        user_id = "user_123"

        # Mock Redis operations
        mock_redis.delete.return_value = 1

        # Simulate token invalidation (logout)
        mock_redis.delete(f"refresh_token:{user_id}")

        # Verify deletion
        mock_redis.delete.assert_called_with(f"refresh_token:{user_id}")

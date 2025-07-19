"""Unit tests for rate limiter utility."""

from unittest.mock import MagicMock, patch

import redis

from src.utils.rate_limiter import RateLimiter


class TestRateLimiter:
    """Test cases for RateLimiter class."""

    def test_rate_limiter_initialization(self):
        """Test rate limiter initialization."""
        rate_limiter = RateLimiter(prefix="test_login", max_attempts=5, time_window=300)

        assert rate_limiter.prefix == "test_login"
        assert rate_limiter.max_attempts == 5
        assert rate_limiter.time_window == 300

    def test_get_key_generation(self):
        """Test Redis key generation."""
        rate_limiter = RateLimiter("login", 5, 300)

        key = rate_limiter._get_key("user@example.com")
        assert key == "login:user@example.com"

        key = rate_limiter._get_key("192.168.1.1")
        assert key == "login:192.168.1.1"

    def test_is_rate_limited_no_attempts(self):
        """Test rate limiting check with no previous attempts."""
        rate_limiter = RateLimiter("login", 5, 300)
        mock_redis = MagicMock(spec=redis.Redis)

        # Mock Redis to return 0 attempts
        mock_redis.zcard.return_value = 0

        result = rate_limiter.is_rate_limited("user@example.com", mock_redis)

        assert result is False
        mock_redis.zcard.assert_called_once_with("login:user@example.com")

    def test_is_rate_limited_under_limit(self):
        """Test rate limiting check under the limit."""
        rate_limiter = RateLimiter("login", 5, 300)
        mock_redis = MagicMock(spec=redis.Redis)

        # Mock Redis to return 3 attempts (under limit of 5)
        mock_redis.zcard.return_value = 3

        result = rate_limiter.is_rate_limited("user@example.com", mock_redis)

        assert result is False

    def test_is_rate_limited_at_limit(self):
        """Test rate limiting check at the limit."""
        rate_limiter = RateLimiter("login", 5, 300)
        mock_redis = MagicMock(spec=redis.Redis)

        # Mock Redis to return 5 attempts (at limit)
        mock_redis.zcard.return_value = 5

        result = rate_limiter.is_rate_limited("user@example.com", mock_redis)

        assert result is True

    def test_is_rate_limited_over_limit(self):
        """Test rate limiting check over the limit."""
        rate_limiter = RateLimiter("login", 5, 300)
        mock_redis = MagicMock(spec=redis.Redis)

        # Mock Redis to return 7 attempts (over limit)
        mock_redis.zcard.return_value = 7

        result = rate_limiter.is_rate_limited("user@example.com", mock_redis)

        assert result is True

    @patch("time.time")
    def test_increment_rate_limit(self, mock_time):
        """Test incrementing rate limit attempts."""
        mock_time.return_value = 1640995200.0

        rate_limiter = RateLimiter("login", 5, 300)
        mock_redis = MagicMock(spec=redis.Redis)

        rate_limiter.increment_rate_limit("user@example.com", mock_redis)

        # Verify Redis operations
        expected_key = "login:user@example.com"
        expected_score = 1640995200  # int(time.time()) returns integer

        # increment_rate_limit only calls zadd and expire, not zremrangebyscore
        mock_redis.zadd.assert_called_once_with(expected_key, {str(expected_score): expected_score})
        mock_redis.expire.assert_called_once_with(expected_key, 600)  # time_window * 2

    def test_reset_rate_limit(self):
        """Test resetting rate limit attempts."""
        rate_limiter = RateLimiter("login", 5, 300)
        mock_redis = MagicMock(spec=redis.Redis)

        rate_limiter.reset_rate_limit("user@example.com", mock_redis)

        expected_key = "login:user@example.com"
        mock_redis.delete.assert_called_once_with(expected_key)

    def test_get_remaining_attempts(self):
        """Test getting remaining attempt count."""
        rate_limiter = RateLimiter("login", 5, 300)
        mock_redis = MagicMock(spec=redis.Redis)

        # Mock Redis to return 2 attempts used out of 5 max
        mock_redis.zcard.return_value = 2
        mock_redis.zremrangebyscore.return_value = 0

        remaining = rate_limiter.get_remaining_attempts("user@example.com", mock_redis)

        assert remaining == 3  # 5 max - 2 used = 3 remaining
        expected_key = "login:user@example.com"
        mock_redis.zcard.assert_called_with(expected_key)

    @patch("time.time")
    def test_get_time_until_reset(self, mock_time):
        """Test getting time until rate limit reset."""
        mock_time.return_value = 1640995200.0

        rate_limiter = RateLimiter("login", 5, 300)
        mock_redis = MagicMock(spec=redis.Redis)

        # Mock Redis to return oldest attempt timestamp with score
        mock_redis.zrange.return_value = [(b"1640994900.0", 1640994900.0)]

        time_until_reset = rate_limiter.get_time_until_reset("user@example.com", mock_redis)

        # Should be None since oldest attempt + time_window = current time (expired)
        assert time_until_reset is None

        expected_key = "login:user@example.com"
        mock_redis.zrange.assert_called_once_with(expected_key, 0, 0, withscores=True)

    @patch("time.time")
    def test_get_time_until_reset_future(self, mock_time):
        """Test getting time until reset when reset is in the future."""
        mock_time.return_value = 1640995200.0

        rate_limiter = RateLimiter("login", 5, 300)
        mock_redis = MagicMock(spec=redis.Redis)

        # Mock Redis to return recent attempt timestamp with score
        mock_redis.zrange.return_value = [(b"1640995000.0", 1640995000.0)]

        time_until_reset = rate_limiter.get_time_until_reset("user@example.com", mock_redis)

        # Should be 100 seconds (1640995000 + 300 - 1640995200)
        assert time_until_reset == 100

    def test_get_time_until_reset_no_attempts(self):
        """Test getting time until reset with no attempts."""
        rate_limiter = RateLimiter("login", 5, 300)
        mock_redis = MagicMock(spec=redis.Redis)

        # Mock Redis to return empty list
        mock_redis.zrange.return_value = []

        time_until_reset = rate_limiter.get_time_until_reset("user@example.com", mock_redis)

        assert time_until_reset is None

    def test_redis_connection_error_handling(self):
        """Test handling Redis connection errors."""
        rate_limiter = RateLimiter("login", 5, 300)
        mock_redis = MagicMock(spec=redis.Redis)

        # Mock Redis to raise connection error
        mock_redis.zcard.side_effect = redis.ConnectionError("Connection failed")

        # Should not raise exception and return False (not rate limited)
        result = rate_limiter.is_rate_limited("user@example.com", mock_redis)
        assert result is False

    def test_multiple_identifiers(self):
        """Test rate limiting with multiple identifiers."""
        rate_limiter = RateLimiter("login", 2, 300)
        mock_redis = MagicMock(spec=redis.Redis)

        # Mock different attempt counts for different identifiers
        def mock_zcard(key):
            if key == "login:user1@example.com":
                return 1
            elif key == "login:user2@example.com":
                return 2
            return 0

        mock_redis.zcard.side_effect = mock_zcard

        # User1 should not be rate limited (1 < 2)
        result1 = rate_limiter.is_rate_limited("user1@example.com", mock_redis)
        assert result1 is False

        # User2 should be rate limited (2 >= 2)
        result2 = rate_limiter.is_rate_limited("user2@example.com", mock_redis)
        assert result2 is True

    def test_edge_case_zero_max_attempts(self):
        """Test edge case with zero max attempts."""
        rate_limiter = RateLimiter("login", 0, 300)
        mock_redis = MagicMock(spec=redis.Redis)

        # With 0 max attempts, any attempt count >= 0 should trigger rate limiting
        mock_redis.zcard.return_value = 0
        mock_redis.zremrangebyscore.return_value = 0
        result = rate_limiter.is_rate_limited("user@example.com", mock_redis)
        assert result is True

    def test_edge_case_zero_time_window(self):
        """Test edge case with zero time window."""
        rate_limiter = RateLimiter("login", 5, 0)
        mock_redis = MagicMock(spec=redis.Redis)

        with patch("time.time", return_value=1640995200.0):
            rate_limiter.increment_rate_limit("user@example.com", mock_redis)

            # increment_rate_limit only calls zadd and expire, not zremrangebyscore
            expected_key = "login:user@example.com"
            mock_redis.zadd.assert_called_once_with(
                expected_key,
                {str(1640995200): 1640995200},  # int(time.time()) returns integer
            )
            mock_redis.expire.assert_called_once_with(expected_key, 0)  # time_window * 2 = 0

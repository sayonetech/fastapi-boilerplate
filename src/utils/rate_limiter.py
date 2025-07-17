"""Rate limiter utility for preventing abuse and brute force attacks."""

import logging
import time

import redis

logger = logging.getLogger(__name__)


class RateLimiter:
    """
    Redis-based rate limiter using sliding window approach.

    This implementation uses Redis sorted sets to track attempts within a time window,
    providing accurate rate limiting for login attempts and other operations.
    """

    def __init__(self, prefix: str, max_attempts: int, time_window: int):
        """
        Initialize rate limiter.

        Args:
            prefix: Redis key prefix for this rate limiter
            max_attempts: Maximum number of attempts allowed
            time_window: Time window in seconds
        """
        self.prefix = prefix
        self.max_attempts = max_attempts
        self.time_window = time_window

    def _get_key(self, identifier: str) -> str:
        """
        Generate Redis key for the given identifier.

        Args:
            identifier: Unique identifier (e.g., email, IP address)

        Returns:
            Redis key string
        """
        return f"{self.prefix}:{identifier}"

    def is_rate_limited(self, identifier: str, redis_client: redis.Redis) -> bool:
        """
        Check if the identifier is currently rate limited.

        Args:
            identifier: Unique identifier to check
            redis_client: Redis client instance

        Returns:
            True if rate limited, False otherwise
        """
        try:
            key = self._get_key(identifier)
            current_time = int(time.time())
            window_start_time = current_time - self.time_window

            # Remove expired entries
            redis_client.zremrangebyscore(key, "-inf", window_start_time)

            # Count current attempts
            attempts = redis_client.zcard(key)
            attempts_count = int(attempts) if attempts else 0

            if attempts_count >= self.max_attempts:
                logger.warning(f"Rate limit exceeded for {identifier}: {attempts_count}/{self.max_attempts}")
                return True

            return False

        except Exception:
            logger.exception(f"Error checking rate limit for {identifier}")
            # Fail open - don't block on Redis errors
            return False

    def increment_rate_limit(self, identifier: str, redis_client: redis.Redis) -> None:
        """
        Increment the rate limit counter for the identifier.

        Args:
            identifier: Unique identifier to increment
            redis_client: Redis client instance
        """
        try:
            key = self._get_key(identifier)
            current_time = int(time.time())

            # Add current timestamp to sorted set
            redis_client.zadd(key, {str(current_time): current_time})

            # Set expiration to cleanup old keys (double the time window for safety)
            redis_client.expire(key, self.time_window * 2)

            logger.debug(f"Incremented rate limit for {identifier}")

        except Exception:
            logger.exception(f"Error incrementing rate limit for {identifier}")

    def reset_rate_limit(self, identifier: str, redis_client: redis.Redis) -> None:
        """
        Reset the rate limit counter for the identifier.

        Args:
            identifier: Unique identifier to reset
            redis_client: Redis client instance
        """
        try:
            key = self._get_key(identifier)
            redis_client.delete(key)
            logger.debug(f"Reset rate limit for {identifier}")

        except Exception:
            logger.exception(f"Error resetting rate limit for {identifier}")

    def get_remaining_attempts(self, identifier: str, redis_client: redis.Redis) -> int:
        """
        Get the number of remaining attempts before rate limiting.

        Args:
            identifier: Unique identifier to check
            redis_client: Redis client instance

        Returns:
            Number of remaining attempts
        """
        try:
            key = self._get_key(identifier)
            current_time = int(time.time())
            window_start_time = current_time - self.time_window

            # Remove expired entries
            redis_client.zremrangebyscore(key, "-inf", window_start_time)

            # Count current attempts
            attempts = redis_client.zcard(key)
            remaining = max(0, self.max_attempts - int(attempts))

            return remaining

        except Exception:
            logger.exception(f"Error getting remaining attempts for {identifier}")
            # Fail open - return max attempts on Redis errors
            return self.max_attempts

    def get_time_until_reset(self, identifier: str, redis_client: redis.Redis) -> int | None:
        """
        Get the time in seconds until the rate limit resets.

        Args:
            identifier: Unique identifier to check
            redis_client: Redis client instance

        Returns:
            Seconds until reset, or None if not rate limited
        """
        try:
            key = self._get_key(identifier)
            current_time = int(time.time())

            # Get the oldest entry in the window
            oldest_entries = redis_client.zrange(key, 0, 0, withscores=True)

            if not oldest_entries:
                return None

            oldest_timestamp = int(oldest_entries[0][1])
            reset_time = oldest_timestamp + self.time_window

            if reset_time > current_time:
                return reset_time - current_time

            return None

        except Exception:
            logger.exception(f"Error getting reset time for {identifier}")
            return None


# Pre-configured rate limiters for common use cases
def get_login_rate_limiter() -> RateLimiter:
    """Get login rate limiter with configuration from settings."""
    from ..configs import madcrow_config

    return RateLimiter(
        prefix="login_attempts",
        max_attempts=madcrow_config.RATE_LIMIT_LOGIN_MAX_ATTEMPTS,
        time_window=madcrow_config.RATE_LIMIT_LOGIN_TIME_WINDOW,
    )


# Default instance for backward compatibility
LOGIN_RATE_LIMITER = RateLimiter(
    prefix="login_attempts",
    max_attempts=5,  # 5 failed attempts
    time_window=900,  # 15 minutes
)

REGISTRATION_RATE_LIMITER = RateLimiter(
    prefix="registration_attempts",
    max_attempts=3,  # 3 registration attempts
    time_window=3600,  # 1 hour
)

PASSWORD_RESET_RATE_LIMITER = RateLimiter(
    prefix="password_reset_attempts",
    max_attempts=3,  # 3 password reset attempts
    time_window=3600,  # 1 hour
)

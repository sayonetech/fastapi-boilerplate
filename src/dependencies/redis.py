"""Redis dependency for FastAPI dependency injection."""

import logging
from typing import Annotated, Any, Optional

import redis
from fastapi import Depends, HTTPException

from ..extensions.ext_redis import get_redis, is_redis_available

logger = logging.getLogger(__name__)


def get_redis_client() -> redis.Redis:
    """
    Get Redis client for dependency injection.

    Returns:
        Redis client instance

    Raises:
        HTTPException: If Redis is not available
    """
    try:
        if not is_redis_available():
            raise HTTPException(status_code=503, detail="Redis service is not available")

        return get_redis()

    except Exception as e:
        logger.exception("Failed to get Redis client")
        raise HTTPException(status_code=503, detail=f"Redis connection failed: {str(e)}") from e


def get_optional_redis_client() -> redis.Redis | None:
    """
    Get Redis client for optional dependency injection.

    This dependency returns None if Redis is not available,
    allowing the application to continue without Redis.

    Returns:
        Redis client instance or None if not available
    """
    try:
        if not is_redis_available():
            logger.warning("Redis is not available, returning None")
            return None

        return get_redis()

    except Exception as e:
        logger.exception("Failed to get Redis client, returning None")
        return None


# Type annotations for dependency injection
RedisClient = Annotated[redis.Redis, Depends(get_redis_client)]
OptionalRedisClient = Annotated[Optional[redis.Redis], Depends(get_optional_redis_client)]


class RedisService:
    """
    Redis service wrapper with common operations.

    This class provides high-level Redis operations commonly used
    in web applications like caching, session storage, and pub/sub.
    """

    def __init__(self, client: redis.Redis):
        """
        Initialize Redis service.

        Args:
            client: Redis client instance
        """
        self.client = client

    # Cache operations
    def get_cache(self, key: str) -> str | None:
        """
        Get cached value by key.

        Args:
            key: Cache key

        Returns:
            Cached value or None if not found
        """
        try:
            result = self.client.get(key)
            return str(result) if result is not None else None
        except Exception as e:
            logger.exception(f"Failed to get cache for key {key}")
            return None

    def set_cache(self, key: str, value: str, expire_seconds: int | None = None) -> bool:
        """
        Set cached value with optional expiration.

        Args:
            key: Cache key
            value: Value to cache
            expire_seconds: Expiration time in seconds

        Returns:
            True if successful, False otherwise
        """
        try:
            if expire_seconds:
                result = self.client.setex(key, expire_seconds, value)
                return bool(result)
            else:
                result = self.client.set(key, value)
                return bool(result)
        except Exception as e:
            logger.exception(f"Failed to set cache for key {key}")
            return False

    def delete_cache(self, key: str) -> bool:
        """
        Delete cached value by key.

        Args:
            key: Cache key to delete

        Returns:
            True if key was deleted, False otherwise
        """
        try:
            result = self.client.delete(key)
            return bool(result)
        except Exception as e:
            logger.exception(f"Failed to delete cache for key {key}")
            return False

    def exists(self, key: str) -> bool:
        """
        Check if key exists in Redis.

        Args:
            key: Key to check

        Returns:
            True if key exists, False otherwise
        """
        try:
            result = self.client.exists(key)
            return bool(result)
        except Exception as e:
            logger.exception(f"Failed to check existence of key {key}")
            return False

    # Session operations
    def get_session(self, session_id: str) -> dict | None:
        """
        Get session data by session ID.

        Args:
            session_id: Session identifier

        Returns:
            Session data as dictionary or None if not found
        """
        try:
            import json

            data = self.client.get(f"session:{session_id}")
            if data:
                parsed_data = json.loads(str(data))
                return parsed_data if isinstance(parsed_data, dict) else None
            return None
        except Exception as e:
            logger.exception(f"Failed to get session {session_id}")
            return None

    def set_session(self, session_id: str, data: dict, expire_seconds: int = 3600) -> bool:
        """
        Set session data with expiration.

        Args:
            session_id: Session identifier
            data: Session data to store
            expire_seconds: Session expiration time in seconds (default: 1 hour)

        Returns:
            True if successful, False otherwise
        """
        try:
            import json

            result = self.client.setex(f"session:{session_id}", expire_seconds, json.dumps(data))
            return bool(result)
        except Exception as e:
            logger.exception(f"Failed to set session {session_id}")
            return False

    def delete_session(self, session_id: str) -> bool:
        """
        Delete session by session ID.

        Args:
            session_id: Session identifier to delete

        Returns:
            True if session was deleted, False otherwise
        """
        try:
            result = self.client.delete(f"session:{session_id}")
            return bool(result)
        except Exception as e:
            logger.exception(f"Failed to delete session {session_id}")
            return False

    # Pub/Sub operations
    def publish(self, channel: str, message: str) -> int:
        """
        Publish message to Redis channel.

        Args:
            channel: Channel name
            message: Message to publish

        Returns:
            Number of subscribers that received the message
        """
        try:
            result = self.client.publish(channel, message)
            # Redis publish returns the number of subscribers
            return int(str(result)) if result is not None else 0
        except Exception as e:
            logger.exception(f"Failed to publish to channel {channel}")
            return 0

    def get_pubsub(self) -> Any:
        """
        Get Redis pub/sub client.

        Returns:
            Redis pub/sub client
        """
        return self.client.pubsub()

    # Rate limiting operations
    def is_rate_limited(self, key: str, limit: int, window_seconds: int) -> bool:
        """
        Check if rate limit is exceeded using sliding window.

        Args:
            key: Rate limit key (e.g., user ID, IP address)
            limit: Maximum number of requests allowed
            window_seconds: Time window in seconds

        Returns:
            True if rate limited, False otherwise
        """
        try:
            import time

            now = time.time()
            pipeline = self.client.pipeline()

            # Remove old entries
            pipeline.zremrangebyscore(key, 0, now - window_seconds)

            # Count current entries
            pipeline.zcard(key)

            # Add current request
            pipeline.zadd(key, {str(now): now})

            # Set expiration
            pipeline.expire(key, window_seconds)

            results = pipeline.execute()
            current_count = int(results[1]) if results[1] is not None else 0

            return current_count >= limit

        except Exception as e:
            logger.exception(f"Failed to check rate limit for key {key}")
            return False


def get_redis_service(client: RedisClient) -> RedisService:
    """
    Get Redis service for dependency injection.

    Args:
        client: Redis client from dependency injection

    Returns:
        Redis service instance
    """
    return RedisService(client)


def get_optional_redis_service(client: OptionalRedisClient) -> RedisService | None:
    """
    Get optional Redis service for dependency injection.

    Args:
        client: Optional Redis client from dependency injection

    Returns:
        Redis service instance or None if Redis is not available
    """
    return RedisService(client) if client else None


# Type annotations for Redis service dependency injection
RedisServiceDep = Annotated[RedisService, Depends(get_redis_service)]
OptionalRedisServiceDep = Annotated[Optional[RedisService], Depends(get_optional_redis_service)]

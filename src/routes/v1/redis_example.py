"""Example routes demonstrating Redis usage patterns with enhanced error handling."""

import logging
from typing import Any

from pydantic import BaseModel, Field

from ...dependencies import OptionalRedisServiceDep, RedisServiceDep
from ...exceptions import DatabaseError
from ...utils.error_factory import ErrorFactory
from ..base_router import BaseRouter
from ..cbv import cbv, delete, get, post

logger = logging.getLogger(__name__)


# Request/Response models for demonstration
class CacheRequest(BaseModel):
    """Request model for cache operations."""

    key: str = Field(..., min_length=1, max_length=255, description="Cache key")
    value: str = Field(..., description="Value to cache")
    expire_seconds: int | None = Field(None, gt=0, description="Expiration time in seconds")


class CacheResponse(BaseModel):
    """Response model for cache operations."""

    key: str
    value: str | None = None
    exists: bool
    ttl: int | None = None


class SessionRequest(BaseModel):
    """Request model for session operations."""

    session_id: str = Field(..., min_length=1, description="Session identifier")
    data: dict[str, Any] = Field(..., description="Session data")
    expire_seconds: int = Field(3600, gt=0, description="Session expiration in seconds")


class SessionResponse(BaseModel):
    """Response model for session operations."""

    session_id: str
    data: dict[str, Any] | None = None
    exists: bool


class RateLimitRequest(BaseModel):
    """Request model for rate limiting."""

    key: str = Field(..., min_length=1, description="Rate limit key (e.g., user ID)")
    limit: int = Field(..., gt=0, description="Maximum requests allowed")
    window_seconds: int = Field(..., gt=0, description="Time window in seconds")


class RateLimitResponse(BaseModel):
    """Response model for rate limiting."""

    key: str
    is_limited: bool
    limit: int
    window_seconds: int
    current_count: int | None = None


redis_example_router = BaseRouter(
    prefix="/v1/redis-example",
    tags=["redis-examples"],
)


@cbv(redis_example_router)
class RedisExampleController:
    """Example controller demonstrating Redis usage patterns with enhanced error handling."""

    @get("/health", operation_id="redis_health_check")
    async def health_check(
        self,
        redis_service: OptionalRedisServiceDep,
    ) -> dict[str, Any]:
        """
        Check Redis health and availability.

        This endpoint demonstrates optional Redis dependency usage,
        allowing the application to continue even if Redis is unavailable.
        """
        if not redis_service:
            return {
                "status": "unavailable",
                "message": "Redis service is not available",
                "available": False,
            }

        try:
            # Test Redis connection
            ping_result = redis_service.client.ping()

            # Get Redis info
            info = {}
            try:
                redis_info = redis_service.client.info()
                if isinstance(redis_info, dict):
                    info = redis_info
            except Exception:
                # Info retrieval failed, but don't fail the health check
                logger.debug("Failed to retrieve Redis info for health check")

            return {
                "status": "healthy",
                "message": "Redis is available and responding",
                "available": True,
                "ping": ping_result,
                "version": info.get("redis_version"),
                "connected_clients": info.get("connected_clients"),
                "used_memory_human": info.get("used_memory_human"),
            }

        except Exception as e:
            return {
                "status": "error",
                "message": f"Redis health check failed: {str(e)}",
                "available": False,
            }

    @post("/cache", operation_id="set_cache", response_model=CacheResponse)
    async def set_cache(
        self,
        request: CacheRequest,
        redis_service: RedisServiceDep,
    ) -> CacheResponse:
        """
        Set a value in Redis cache with optional expiration.

        Demonstrates:
        - Cache operations with Redis
        - Error handling for Redis failures
        - Input validation
        """
        try:
            # Set cache value
            success = redis_service.set_cache(
                key=request.key,
                value=request.value,
                expire_seconds=request.expire_seconds,
            )

            # Guard clause for failed operation
            if not success:
                raise ErrorFactory.create_database_error(
                    message="Failed to set cache value",
                    operation="set",
                    table="redis_cache",
                )

            # Get TTL if expiration was set
            ttl = None
            if request.expire_seconds:
                try:
                    ttl_value = redis_service.client.ttl(request.key)
                    if isinstance(ttl_value, int) and ttl_value > 0:
                        ttl = ttl_value
                except Exception:
                    # TTL retrieval failed, but don't fail the whole operation
                    logger.debug(f"Failed to retrieve TTL for key: {request.key}")

            # Happy path - return success response
            return CacheResponse(
                key=request.key,
                value=request.value,
                exists=True,
                ttl=ttl,
            )

        except DatabaseError:
            # Re-raise our custom database errors
            raise
        except Exception as e:
            # Convert unexpected exceptions
            raise ErrorFactory.create_database_error(
                message="Unexpected error during cache set operation",
                operation="set",
                table="redis_cache",
                cause=e,
            )

    @get("/cache/{key}", operation_id="get_cache", response_model=CacheResponse)
    async def get_cache(
        self,
        key: str,
        redis_service: RedisServiceDep,
    ) -> CacheResponse:
        """
        Get a value from Redis cache.

        Demonstrates:
        - Cache retrieval operations
        - Handling cache misses
        - TTL information
        """
        # Early validation
        if not key or len(key.strip()) == 0:
            raise ErrorFactory.create_validation_error(
                field="key",
                message="Cache key cannot be empty",
                value=key,
            )

        try:
            # Get cached value
            value = redis_service.get_cache(key)

            # Check if key exists
            exists = redis_service.exists(key)

            # Get TTL information
            ttl = None
            if exists:
                try:
                    ttl_value = redis_service.client.ttl(key)
                    if isinstance(ttl_value, int) and ttl_value > 0:
                        ttl = ttl_value
                except Exception:
                    # TTL retrieval failed, but don't fail the whole operation
                    logger.debug(f"Failed to retrieve TTL for key: {key}")

            return CacheResponse(
                key=key,
                value=value,
                exists=exists,
                ttl=ttl,
            )

        except Exception as e:
            # Convert unexpected exceptions
            raise ErrorFactory.create_database_error(
                message="Failed to retrieve cache value",
                operation="get",
                table="redis_cache",
                cause=e,
            )

    @delete("/cache/{key}", operation_id="delete_cache")
    async def delete_cache(
        self,
        key: str,
        redis_service: RedisServiceDep,
    ) -> dict[str, Any]:
        """
        Delete a value from Redis cache.

        Demonstrates:
        - Cache deletion operations
        - Handling non-existent keys
        """
        # Early validation
        if not key or len(key.strip()) == 0:
            raise ErrorFactory.create_validation_error(
                field="key",
                message="Cache key cannot be empty",
                value=key,
            )

        try:
            # Check if key exists before deletion
            exists_before = redis_service.exists(key)

            # Delete the key
            deleted = redis_service.delete_cache(key)

            return {
                "key": key,
                "deleted": deleted,
                "existed": exists_before,
                "message": "Cache key deleted successfully" if deleted else "Cache key did not exist",
            }

        except Exception as e:
            # Convert unexpected exceptions
            raise ErrorFactory.create_database_error(
                message="Failed to delete cache value",
                operation="delete",
                table="redis_cache",
                cause=e,
            )

    @post("/session", operation_id="set_session", response_model=SessionResponse)
    async def set_session(
        self,
        request: SessionRequest,
        redis_service: RedisServiceDep,
    ) -> SessionResponse:
        """
        Set session data in Redis.

        Demonstrates:
        - Session storage with JSON serialization
        - Session expiration handling
        """
        try:
            # Set session data
            success = redis_service.set_session(
                session_id=request.session_id,
                data=request.data,
                expire_seconds=request.expire_seconds,
            )

            # Guard clause for failed operation
            if not success:
                raise ErrorFactory.create_database_error(
                    message="Failed to set session data",
                    operation="set",
                    table="redis_sessions",
                )

            # Happy path - return success response
            return SessionResponse(
                session_id=request.session_id,
                data=request.data,
                exists=True,
            )

        except DatabaseError:
            # Re-raise our custom database errors
            raise
        except Exception as e:
            # Convert unexpected exceptions
            raise ErrorFactory.create_database_error(
                message="Unexpected error during session set operation",
                operation="set",
                table="redis_sessions",
                cause=e,
            )

    @get("/session/{session_id}", operation_id="get_session", response_model=SessionResponse)
    async def get_session(
        self,
        session_id: str,
        redis_service: RedisServiceDep,
    ) -> SessionResponse:
        """
        Get session data from Redis.

        Demonstrates:
        - Session retrieval with JSON deserialization
        - Handling missing sessions
        """
        # Early validation
        if not session_id or len(session_id.strip()) == 0:
            raise ErrorFactory.create_validation_error(
                field="session_id",
                message="Session ID cannot be empty",
                value=session_id,
            )

        try:
            # Get session data
            data = redis_service.get_session(session_id)

            return SessionResponse(
                session_id=session_id,
                data=data,
                exists=data is not None,
            )

        except Exception as e:
            # Convert unexpected exceptions
            raise ErrorFactory.create_database_error(
                message="Failed to retrieve session data",
                operation="get",
                table="redis_sessions",
                cause=e,
            )

    @delete("/session/{session_id}", operation_id="delete_session")
    async def delete_session(
        self,
        session_id: str,
        redis_service: RedisServiceDep,
    ) -> dict[str, Any]:
        """
        Delete session data from Redis.

        Demonstrates:
        - Session cleanup operations
        """
        # Early validation
        if not session_id or len(session_id.strip()) == 0:
            raise ErrorFactory.create_validation_error(
                field="session_id",
                message="Session ID cannot be empty",
                value=session_id,
            )

        try:
            # Delete session
            deleted = redis_service.delete_session(session_id)

            return {
                "session_id": session_id,
                "deleted": deleted,
                "message": "Session deleted successfully" if deleted else "Session did not exist",
            }

        except Exception as e:
            # Convert unexpected exceptions
            raise ErrorFactory.create_database_error(
                message="Failed to delete session data",
                operation="delete",
                table="redis_sessions",
                cause=e,
            )

    @post("/rate-limit/check", operation_id="check_rate_limit", response_model=RateLimitResponse)
    async def check_rate_limit(
        self,
        request: RateLimitRequest,
        redis_service: RedisServiceDep,
    ) -> RateLimitResponse:
        """
        Check if a key is rate limited using sliding window algorithm.

        Demonstrates:
        - Rate limiting with Redis sorted sets
        - Sliding window rate limiting algorithm
        - Complex Redis operations
        """
        try:
            # Check rate limit
            is_limited = redis_service.is_rate_limited(
                key=f"rate_limit:{request.key}",
                limit=request.limit,
                window_seconds=request.window_seconds,
            )

            # Get current count for informational purposes
            current_count = None
            try:
                count_value = redis_service.client.zcard(f"rate_limit:{request.key}")
                if isinstance(count_value, int):
                    current_count = count_value
            except Exception:
                # Don't fail the whole operation if we can't get the count
                logger.debug(f"Failed to retrieve rate limit count for key: {request.key}")

            return RateLimitResponse(
                key=request.key,
                is_limited=is_limited,
                limit=request.limit,
                window_seconds=request.window_seconds,
                current_count=current_count,
            )

        except Exception as e:
            # Convert unexpected exceptions
            raise ErrorFactory.create_database_error(
                message="Failed to check rate limit",
                operation="rate_limit_check",
                table="redis_rate_limits",
                cause=e,
            )

    @post("/pub-sub/publish/{channel}", operation_id="publish_message")
    async def publish_message(
        self,
        channel: str,
        message: str,
        redis_service: RedisServiceDep,
    ) -> dict[str, Any]:
        """
        Publish a message to a Redis channel.

        Demonstrates:
        - Redis pub/sub functionality
        - Message publishing
        """
        # Early validation
        if not channel or len(channel.strip()) == 0:
            raise ErrorFactory.create_validation_error(
                field="channel",
                message="Channel name cannot be empty",
                value=channel,
            )

        if not message:
            raise ErrorFactory.create_validation_error(
                field="message",
                message="Message cannot be empty",
                value=message,
            )

        try:
            # Publish message
            subscriber_count = redis_service.publish(channel, message)

            return {
                "channel": channel,
                "message": message,
                "subscriber_count": subscriber_count,
                "published": True,
            }

        except Exception as e:
            # Convert unexpected exceptions
            raise ErrorFactory.create_database_error(
                message="Failed to publish message",
                operation="publish",
                table="redis_pubsub",
                cause=e,
            )

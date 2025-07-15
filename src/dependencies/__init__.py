"""Dependencies package for FastAPI dependency injection."""

from .db import (
    DatabaseSession,
    OptionalDatabaseSession,
    get_session,
    get_session_no_exception,
)
from .redis import (
    OptionalRedisClient,
    OptionalRedisServiceDep,
    RedisClient,
    RedisService,
    RedisServiceDep,
    get_optional_redis_client,
    get_optional_redis_service,
    get_redis_client,
    get_redis_service,
)

__all__ = [
    "DatabaseSession",
    "OptionalDatabaseSession",
    "OptionalRedisClient",
    "OptionalRedisServiceDep",
    "RedisClient",
    "RedisService",
    "RedisServiceDep",
    "get_optional_redis_client",
    "get_optional_redis_service",
    "get_redis_client",
    "get_redis_service",
    "get_session",
    "get_session_no_exception",
]

"""Dependencies package for FastAPI dependency injection."""

from .auth import (
    AuthServiceDep,
    ClientIP,
    CurrentAdminUser,
    CurrentUser,
    CurrentUserOptional,
    get_auth_service_dep,
    get_client_ip,
    get_current_admin_user,
    get_jwt_token_from_request,
)
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
    "AuthServiceDep",
    "ClientIP",
    "CurrentAdminUser",
    "CurrentUser",
    "CurrentUserOptional",
    "DatabaseSession",
    "OptionalDatabaseSession",
    "OptionalRedisClient",
    "OptionalRedisServiceDep",
    "RedisClient",
    "RedisService",
    "RedisServiceDep",
    "get_auth_service_dep",
    "get_client_ip",
    "get_current_admin_user",
    "get_jwt_token_from_request",
    "get_optional_redis_client",
    "get_optional_redis_service",
    "get_redis_client",
    "get_redis_service",
    "get_session",
    "get_session_no_exception",
]

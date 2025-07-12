"""Redis extension for FastAPI application."""

import logging
from typing import Any

import redis
from redis.connection import ConnectionPool
from redis.sentinel import Sentinel

from ..beco_app import BecoApp
from ..configs import madcrow_config

logger = logging.getLogger(__name__)


class Redis:
    """
    Redis client wrapper with connection pooling and sentinel support.

    This class provides a unified interface for Redis operations with support for:
    - Standard Redis connections
    - Redis Sentinel for high availability
    - Connection pooling for better performance
    - SSL/TLS connections
    - Authentication
    """

    def __init__(self) -> None:
        """Initialize Redis wrapper without connecting."""
        self._client: redis.Redis | None = None
        self._pool: ConnectionPool | None = None
        self._sentinel: Sentinel | None = None
        self._is_initialized = False

    def initialize(self, app: BecoApp | None = None) -> None:
        """
        Initialize Redis connection based on configuration.

        Args:
            app: FastAPI application instance (optional)
        """
        try:
            logger.info("Initializing Redis connection...")

            # Use Sentinel if configured
            if madcrow_config.REDIS_USE_SENTINEL:
                self._initialize_sentinel()
            else:
                self._initialize_direct()

            # Test the connection
            self._test_connection()

            self._is_initialized = True
            logger.info("Redis connection initialized successfully")

        except Exception as e:
            logger.exception("Failed to initialize Redis connection")
            if madcrow_config.DEPLOY_ENV == "PRODUCTION":
                raise RuntimeError(f"Redis initialization failed: {e}") from e
            else:
                logger.warning("Redis connection failed, but continuing in development mode")

    def _initialize_sentinel(self) -> None:
        """Initialize Redis connection using Sentinel."""
        logger.info("Initializing Redis with Sentinel configuration")

        # Parse sentinel nodes
        sentinel_nodes = []
        if madcrow_config.REDIS_SENTINELS:
            for node in madcrow_config.REDIS_SENTINELS.split(","):
                host, port = node.strip().split(":")
                sentinel_nodes.append((host, int(port)))

        if not sentinel_nodes:
            raise ValueError("REDIS_SENTINELS must be configured when using Sentinel")

        # Create Sentinel instance
        self._sentinel = Sentinel(
            sentinel_nodes,
            sentinel_kwargs={
                "username": madcrow_config.REDIS_SENTINEL_USERNAME,
                "password": madcrow_config.REDIS_SENTINEL_PASSWORD,
                "socket_timeout": madcrow_config.REDIS_SENTINEL_SOCKET_TIMEOUT,
            },
        )

        # Get master connection
        self._client = self._sentinel.master_for(
            madcrow_config.REDIS_SENTINEL_SERVICE_NAME,
            username=madcrow_config.REDIS_USERNAME,
            password=madcrow_config.REDIS_PASSWORD,
            db=madcrow_config.REDIS_DB,
            ssl=madcrow_config.REDIS_USE_SSL,
            decode_responses=True,
        )

    def _initialize_direct(self) -> None:
        """Initialize direct Redis connection."""
        logger.info("Initializing direct Redis connection")

        # Prepare connection parameters
        connection_params = {
            "host": madcrow_config.REDIS_HOST,
            "port": madcrow_config.REDIS_PORT,
            "db": madcrow_config.REDIS_DB,
            "decode_responses": True,
            "max_connections": 20,  # Default pool size
            "retry_on_timeout": True,
            "health_check_interval": 30,
        }

        # Add optional parameters only if they have values
        if madcrow_config.REDIS_USERNAME:
            connection_params["username"] = madcrow_config.REDIS_USERNAME

        if madcrow_config.REDIS_PASSWORD:
            connection_params["password"] = madcrow_config.REDIS_PASSWORD

        # Handle SSL parameter carefully
        if madcrow_config.REDIS_USE_SSL:
            connection_params["ssl"] = True
            connection_params["ssl_check_hostname"] = False
            connection_params["ssl_cert_reqs"] = None

        # Create connection pool
        self._pool = ConnectionPool.from_url(
            f"redis://{madcrow_config.REDIS_HOST}:{madcrow_config.REDIS_PORT}/{madcrow_config.REDIS_DB}",
            **{k: v for k, v in connection_params.items() if k not in ["host", "port", "db"]},
        )

        # Create Redis client
        self._client = redis.Redis(connection_pool=self._pool)

    def _test_connection(self) -> None:
        """Test Redis connection."""
        if not self._client:
            raise RuntimeError("Redis client not initialized")

        try:
            # Simple ping test
            result = self._client.ping()
            if not result:
                raise RuntimeError("Redis ping failed")

            logger.debug("Redis connection test successful")

        except Exception:
            logger.exception("Redis connection test failed")
            raise

    def get_client(self) -> redis.Redis:
        """
        Get the Redis client instance.

        Returns:
            Redis client instance

        Raises:
            RuntimeError: If Redis is not initialized
        """
        if not self._is_initialized or not self._client:
            raise RuntimeError("Redis not initialized. Call initialize() first.")

        return self._client

    def is_available(self) -> bool:
        """
        Check if Redis is available.

        Returns:
            True if Redis is available, False otherwise
        """
        if not self._is_initialized or not self._client:
            return False

        try:
            result = self._client.ping()
            return bool(result)
        except Exception:
            return False

    def close(self) -> None:
        """Close Redis connections."""
        try:
            if self._client:
                self._client.close()
            if self._pool:
                self._pool.disconnect()

            self._client = None
            self._pool = None
            self._sentinel = None
            self._is_initialized = False

            logger.info("Redis connections closed")

        except Exception:
            logger.exception("Error closing Redis connections")

    def __getattr__(self, name: str) -> Any:
        """
        Proxy attribute access to the Redis client.

        Args:
            name: Attribute name

        Returns:
            Redis client attribute
        """
        if not self._is_initialized or not self._client:
            raise RuntimeError("Redis not initialized. Call initialize() first.")

        return getattr(self._client, name)


# Global Redis instance
redis_client = Redis()


def init_app(app: BecoApp) -> None:
    """
    Initialize Redis extension for the FastAPI application.

    Args:
        app: FastAPI application instance
    """
    try:
        logger.info("Initializing Redis extension...")

        # Initialize Redis connection
        redis_client.initialize(app)

        # Log configuration in debug mode
        if madcrow_config.DEBUG:
            _log_redis_config()

        logger.info("Redis extension initialized successfully")

    except Exception as e:
        logger.exception("Failed to initialize Redis extension")
        if madcrow_config.DEPLOY_ENV == "PRODUCTION":
            raise RuntimeError(f"Redis extension initialization failed: {e}") from e
        else:
            logger.warning("Redis extension initialization failed, but continuing in development mode")


def cleanup() -> None:
    """Cleanup Redis resources. Called by lifespan manager."""
    redis_client.close()


def _log_redis_config() -> None:
    """Log Redis configuration for debugging."""
    config_info = {
        "host": madcrow_config.REDIS_HOST,
        "port": madcrow_config.REDIS_PORT,
        "db": madcrow_config.REDIS_DB,
        "use_ssl": madcrow_config.REDIS_USE_SSL,
        "use_sentinel": madcrow_config.REDIS_USE_SENTINEL,
        "has_password": bool(madcrow_config.REDIS_PASSWORD),
        "has_username": bool(madcrow_config.REDIS_USERNAME),
    }

    if madcrow_config.REDIS_USE_SENTINEL:
        config_info.update(
            {
                "sentinel_service": madcrow_config.REDIS_SENTINEL_SERVICE_NAME,
                "sentinel_nodes": madcrow_config.REDIS_SENTINELS,
            }
        )

    logger.debug("Redis configuration:", extra=config_info)


def get_redis() -> redis.Redis:
    """
    Get the global Redis client instance.

    Returns:
        Redis client instance

    Raises:
        RuntimeError: If Redis is not initialized
    """
    return redis_client.get_client()


def is_redis_available() -> bool:
    """
    Check if Redis is available.

    Returns:
        True if Redis is available, False otherwise
    """
    return redis_client.is_available()

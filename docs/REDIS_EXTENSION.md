# Redis Extension

This document describes the Redis extension implementation for the FastAPI Madcrow project.

## Overview

The Redis extension provides comprehensive Redis functionality including:

- **Connection Management**: Automatic connection pooling and health monitoring
- **High Availability**: Redis Sentinel support for production deployments
- **Caching**: High-level caching operations with TTL support
- **Sessions**: JSON-based session storage with expiration
- **Rate Limiting**: Sliding window rate limiting using sorted sets
- **Pub/Sub**: Message publishing and subscription capabilities
- **Dependency Injection**: FastAPI-compatible dependency injection

## Architecture

### Core Components

1. **Redis Extension** (`src/extensions/ext_redis.py`)
   - Connection management and initialization
   - Support for direct connections and Redis Sentinel
   - Health monitoring and graceful degradation

2. **Redis Dependencies** (`src/dependencies/redis.py`)
   - FastAPI dependency injection support
   - High-level Redis service wrapper
   - Optional dependencies for graceful degradation

3. **Configuration** (`src/configs/enviornment/redis_config.py`)
   - Comprehensive Redis configuration options
   - Support for Sentinel and cluster configurations

## Configuration

### Environment Variables

The following environment variables are supported for Redis configuration:

#### Basic Redis Configuration

```bash
# Redis server connection
REDIS_HOST=localhost                    # Redis host
REDIS_PORT=6379                        # Redis port
REDIS_DB=0                             # Redis database number
REDIS_USERNAME=                        # Redis username (optional)
REDIS_PASSWORD=                        # Redis password (optional)
REDIS_USE_SSL=false                    # Enable SSL/TLS

# Connection pooling
REDIS_MAX_CONNECTIONS=20               # Maximum connections in pool
```

#### Redis Sentinel Configuration (High Availability)

```bash
# Sentinel mode
REDIS_USE_SENTINEL=false               # Enable Sentinel mode
REDIS_SENTINELS=host1:26379,host2:26379,host3:26379  # Sentinel nodes
REDIS_SENTINEL_SERVICE_NAME=mymaster   # Sentinel service name
REDIS_SENTINEL_USERNAME=               # Sentinel username (optional)
REDIS_SENTINEL_PASSWORD=               # Sentinel password (optional)
REDIS_SENTINEL_SOCKET_TIMEOUT=0.1      # Sentinel timeout in seconds
```

#### Redis Cluster Configuration (Future Support)

```bash
# Cluster mode (for future implementation)
REDIS_USE_CLUSTERS=false               # Enable cluster mode
REDIS_CLUSTERS=host1:7000,host2:7000   # Cluster nodes
REDIS_CLUSTERS_PASSWORD=               # Cluster password (optional)
```

## Usage Examples

### Basic Usage with Dependency Injection

```python
from fastapi import APIRouter
from src.dependencies import RedisServiceDep
from src.routes.cbv import cbv, get, post

router = APIRouter()

@cbv(router)
class MyController:
    @get("/cache/{key}")
    async def get_cached_data(
        self,
        key: str,
        redis_service: RedisServiceDep,
    ) -> dict:
        """Get cached data."""
        value = await redis_service.get_cache(key)
        return {"key": key, "value": value, "exists": value is not None}

    @post("/cache")
    async def set_cached_data(
        self,
        key: str,
        value: str,
        expire_seconds: int = 3600,
        redis_service: RedisServiceDep,
    ) -> dict:
        """Set cached data with expiration."""
        success = await redis_service.set_cache(key, value, expire_seconds)
        return {"success": success, "key": key}
```

### Optional Redis Usage (Graceful Degradation)

```python
from src.dependencies import OptionalRedisServiceDep

@cbv(router)
class MyController:
    @get("/data/{id}")
    async def get_data(
        self,
        id: str,
        redis_service: OptionalRedisServiceDep,
    ) -> dict:
        """Get data with optional caching."""
        # Try to get from cache first
        if redis_service:
            cached = await redis_service.get_cache(f"data:{id}")
            if cached:
                return {"data": cached, "source": "cache"}

        # Fallback to database or other source
        data = await get_data_from_database(id)

        # Cache for next time if Redis is available
        if redis_service:
            await redis_service.set_cache(f"data:{id}", data, 300)

        return {"data": data, "source": "database"}
```

### Session Management

```python
@post("/login")
async def login(
    credentials: LoginRequest,
    redis_service: RedisServiceDep,
) -> dict:
    """Login and create session."""
    # Authenticate user
    user = await authenticate_user(credentials)

    # Create session
    session_id = str(uuid4())
    session_data = {
        "user_id": user.id,
        "username": user.username,
        "role": user.role,
        "login_time": datetime.utcnow().isoformat(),
    }

    # Store session with 24-hour expiration
    await redis_service.set_session(session_id, session_data, 86400)

    return {"session_id": session_id, "user": user.username}

@get("/profile")
async def get_profile(
    session_id: str,
    redis_service: RedisServiceDep,
) -> dict:
    """Get user profile from session."""
    session_data = await redis_service.get_session(session_id)

    if not session_data:
        raise HTTPException(status_code=401, detail="Invalid session")

    return {"user": session_data}
```

### Rate Limiting

```python
from fastapi import HTTPException

@post("/api/action")
async def rate_limited_action(
    request: Request,
    redis_service: RedisServiceDep,
) -> dict:
    """Action with rate limiting."""
    # Use client IP for rate limiting
    client_ip = request.client.host

    # Check rate limit: 10 requests per minute
    is_limited = await redis_service.is_rate_limited(
        key=f"api_action:{client_ip}",
        limit=10,
        window_seconds=60
    )

    if is_limited:
        raise HTTPException(
            status_code=429,
            detail="Rate limit exceeded. Try again later."
        )

    # Perform the action
    result = await perform_action()
    return {"result": result}
```

### Pub/Sub Messaging

```python
@post("/notify/{channel}")
async def send_notification(
    channel: str,
    message: str,
    redis_service: RedisServiceDep,
) -> dict:
    """Send notification via pub/sub."""
    subscriber_count = await redis_service.publish(channel, message)

    return {
        "channel": channel,
        "message": message,
        "subscribers": subscriber_count,
    }

# Subscriber example (typically in a background task)
async def notification_subscriber():
    """Subscribe to notifications."""
    redis_client = get_redis()
    pubsub = redis_client.pubsub()

    await pubsub.subscribe("notifications")

    async for message in pubsub.listen():
        if message["type"] == "message":
            await handle_notification(message["data"])
```

## Advanced Features

### Custom Redis Operations

```python
from src.extensions.ext_redis import get_redis

async def custom_redis_operation():
    """Perform custom Redis operations."""
    redis_client = get_redis()

    # Use Redis pipeline for batch operations
    pipeline = redis_client.pipeline()
    pipeline.set("key1", "value1")
    pipeline.set("key2", "value2")
    pipeline.expire("key1", 300)
    results = pipeline.execute()

    # Use Redis transactions
    with redis_client.pipeline() as pipe:
        while True:
            try:
                pipe.watch("counter")
                current_value = pipe.get("counter")
                pipe.multi()
                pipe.set("counter", int(current_value or 0) + 1)
                pipe.execute()
                break
            except redis.WatchError:
                continue
```

### Health Monitoring

```python
from src.extensions.ext_redis import is_redis_available

@get("/health")
async def health_check() -> dict:
    """Application health check including Redis."""
    redis_status = "healthy" if is_redis_available() else "unavailable"

    return {
        "status": "healthy",
        "services": {
            "redis": redis_status,
            "database": "healthy",  # Add other service checks
        }
    }
```

## Error Handling

The Redis extension integrates with the enhanced error handling system:

```python
from src.exceptions import DatabaseError
from src.utils.error_factory import ErrorFactory

@get("/cache/{key}")
async def get_cache_with_error_handling(
    key: str,
    redis_service: RedisServiceDep,
) -> dict:
    """Get cache with proper error handling."""
    try:
        value = await redis_service.get_cache(key)
        return {"key": key, "value": value}

    except Exception as e:
        # Convert to standardized error
        raise ErrorFactory.create_database_error(
            message="Failed to retrieve cached data",
            operation="get",
            table="redis_cache",
            cause=e,
        )
```

## Testing

Run the Redis extension tests:

```bash
# Make sure Redis is running
redis-server

# Run the test suite
uv run python test_redis_extension.py
```

The test suite covers:

- Basic Redis operations
- API endpoint functionality
- Service layer operations
- Error handling scenarios
- Rate limiting behavior

## Production Deployment

### Redis Sentinel Setup

For production deployments, use Redis Sentinel for high availability:

```bash
# Environment configuration for Sentinel
REDIS_USE_SENTINEL=true
REDIS_SENTINELS=sentinel1:26379,sentinel2:26379,sentinel3:26379
REDIS_SENTINEL_SERVICE_NAME=mymaster
REDIS_SENTINEL_PASSWORD=your_sentinel_password
```

### Performance Considerations

1. **Connection Pooling**: The extension uses connection pooling by default
2. **Memory Management**: Monitor Redis memory usage and configure appropriate eviction policies
3. **Persistence**: Configure Redis persistence based on your data durability requirements
4. **Monitoring**: Use Redis monitoring tools to track performance metrics

### Security Best Practices

1. **Authentication**: Always use Redis AUTH in production
2. **Network Security**: Use SSL/TLS for Redis connections
3. **Access Control**: Implement Redis ACLs for fine-grained access control
4. **Firewall**: Restrict Redis port access to authorized servers only

## Integration Features

This Redis extension provides comprehensive Redis functionality including:

- **Flexible Configuration**: Supports multiple environment variable formats
- **Sentinel Support**: Full Redis Sentinel support for high availability
- **Connection Pooling**: Efficient connection management
- **Error Handling**: Integrated with the application's error handling system
- **FastAPI Integration**: Native FastAPI dependency injection support

The extension provides production-ready Redis integration with FastAPI-specific features and comprehensive error handling.

# Rate Limiting Implementation

This document describes the rate limiting implementation for the FastAPI Madcrow project, specifically for login attempts to prevent brute force attacks.

## Overview

The rate limiting system uses Redis to track failed login attempts per email address using a sliding window approach. This provides accurate rate limiting that prevents abuse while allowing legitimate users to continue accessing the system.

## Features

- **Sliding Window Rate Limiting**: Uses Redis sorted sets for accurate tracking
- **Configurable Limits**: Max attempts and time window can be configured via environment variables
- **Automatic Reset**: Rate limits are automatically reset on successful login
- **Graceful Degradation**: System continues to work even if Redis is unavailable
- **Proper HTTP Responses**: Returns HTTP 429 with appropriate headers and retry information

## Configuration

Rate limiting can be configured using environment variables:

```bash
# Enable/disable rate limiting
RATE_LIMIT_LOGIN_ENABLED=true

# Maximum failed attempts before rate limiting (default: 5)
RATE_LIMIT_LOGIN_MAX_ATTEMPTS=5

# Time window in seconds (default: 900 = 15 minutes)
RATE_LIMIT_LOGIN_TIME_WINDOW=900
```

## Implementation Details

### Core Components

1. **RateLimiter Class** (`src/utils/rate_limiter.py`)
   - Generic rate limiter using Redis sorted sets
   - Sliding window approach for accurate tracking
   - Methods for checking, incrementing, and resetting limits

2. **Rate Limit Exception** (`src/exceptions/business.py`)
   - `RateLimitExceededError` for handling rate limit violations
   - Includes context information for proper HTTP responses

3. **Pydantic Models** (`src/models/rate_limit.py`)
   - Response models for rate limit information
   - Structured error responses with retry information

4. **Auth Service Integration** (`src/services/auth_service.py`)
   - Rate limiting integrated into login flow
   - Increments on failed attempts, resets on success

5. **HTTP Route Handling** (`src/routes/v1/auth.py`)
   - Proper HTTP 429 responses with retry headers
   - Structured error responses

### Rate Limiting Flow

1. **Pre-Authentication Check**
   - Check if email is currently rate limited
   - Return HTTP 429 if limit exceeded

2. **Failed Authentication**
   - Increment rate limit counter for the email
   - Continue with normal authentication error response

3. **Successful Authentication**
   - Reset rate limit counter for the email
   - Proceed with normal login flow

### Redis Data Structure

The rate limiter uses Redis sorted sets with the following structure:

```
Key: "login_attempts:{email}"
Value: Sorted set of timestamps
Score: Unix timestamp
Member: Unix timestamp (same as score)
```

This allows for efficient:

- Removal of expired entries
- Counting current attempts
- Finding oldest entry for reset time calculation

## Usage Examples

### Basic Rate Limiter Usage

```python
from src.utils.rate_limiter import get_login_rate_limiter
import redis

# Get configured rate limiter
rate_limiter = get_login_rate_limiter()
redis_client = redis.Redis()

# Check if rate limited
if rate_limiter.is_rate_limited("user@example.com", redis_client):
    print("Rate limited!")

# Increment on failed attempt
rate_limiter.increment_rate_limit("user@example.com", redis_client)

# Reset on successful login
rate_limiter.reset_rate_limit("user@example.com", redis_client)
```

### HTTP Response Examples

**Successful Login (200)**

```json
{
  "result": "success",
  "data": {
    "access_token": "...",
    "refresh_token": "...",
    "token_type": "Bearer",
    "expires_in": 3600
  }
}
```

**Rate Limited (429)**

```json
{
  "detail": {
    "result": "error",
    "message": "Rate limit exceeded for user@example.com. Try again in 847 seconds.",
    "error_code": "RATE_LIMIT_EXCEEDED",
    "rate_limit_info": {
      "is_limited": true,
      "remaining_attempts": 0,
      "max_attempts": 5,
      "time_window": 900,
      "time_until_reset": 847
    },
    "retry_after": 847
  }
}
```

**Headers**

```
HTTP/1.1 429 Too Many Requests
Retry-After: 847
Content-Type: application/json
```

## Testing

Run the rate limiter tests:

```bash
# Test basic rate limiter functionality
python test_rate_limiter.py

# Test with actual application
# 1. Start the application
python main.py

# 2. Run integration tests
python test_rate_limiter.py
```

## Security Considerations

1. **Redis Security**: Ensure Redis is properly secured and not exposed publicly
2. **Rate Limit Bypass**: Consider implementing additional rate limiting by IP address
3. **Memory Usage**: Old rate limit keys are automatically cleaned up with TTL
4. **Distributed Systems**: Rate limits are shared across all application instances

## Monitoring

Monitor rate limiting effectiveness:

1. **Redis Metrics**: Track rate limit key counts and memory usage
2. **Application Logs**: Monitor rate limit violations and patterns
3. **HTTP Metrics**: Track 429 response rates and retry patterns

## Troubleshooting

### Common Issues

1. **Redis Connection Errors**
   - Rate limiting is disabled if Redis is unavailable
   - Check Redis connectivity and configuration

2. **Rate Limits Not Working**
   - Verify `RATE_LIMIT_LOGIN_ENABLED=true`
   - Check Redis key expiration and cleanup

3. **False Positives**
   - Adjust `RATE_LIMIT_LOGIN_MAX_ATTEMPTS` if too restrictive
   - Consider implementing IP-based rate limiting for shared accounts

### Debug Commands

```bash
# Check Redis keys
redis-cli KEYS "login_attempts:*"

# View rate limit data for specific email
redis-cli ZRANGE "login_attempts:user@example.com" 0 -1 WITHSCORES

# Clear rate limit for testing
redis-cli DEL "login_attempts:user@example.com"
```

## Future Enhancements

1. **IP-based Rate Limiting**: Additional protection by client IP
2. **Adaptive Rate Limiting**: Dynamic limits based on threat detection
3. **Whitelist/Blacklist**: Bypass or enhanced limits for specific users/IPs
4. **Analytics Dashboard**: Visual monitoring of rate limiting patterns
5. **CAPTCHA Integration**: Challenge-response for rate limited users

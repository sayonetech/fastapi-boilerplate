# API Reference

Quick reference for the Madcrow Backend API endpoints.

## Authentication Endpoints

All authentication endpoints return standard responses with `{"result": "success", "data": {...}}` format.

### Registration

```http
POST /api/v1/auth/register
Content-Type: application/json

{
  "name": "string",
  "email": "string",
  "password": "string"
}
```

**Response**: Token pair with access and refresh tokens

### Login

```http
POST /api/v1/auth/login
Content-Type: application/json

{
  "email": "string",
  "password": "string",
  "remember_me": boolean
}
```

**Response**: Token pair with access and refresh tokens

### Token Refresh

```http
POST /api/v1/auth/refresh-token
Content-Type: application/json

{
  "refresh_token": "string"
}
```

**Response**: New token pair

### Current User

```http
GET /api/v1/auth/me
Authorization: Bearer <access_token>
```

**Response**: User profile information

### Session Validation

```http
GET /api/v1/auth/session/validate
Authorization: Bearer <access_token>
```

**Response**: Session validation status and user info

### Logout

```http
POST /api/v1/auth/logout
Authorization: Bearer <access_token>

{
  "session_id": "string (optional)"
}
```

**Response**: Logout confirmation

### Logout All Sessions

```http
POST /api/v1/auth/logout-all
Authorization: Bearer <access_token>
```

**Response**: Logout confirmation with session count

## Health Endpoints

### Application Health

```http
GET /api/v1/health
```

**Response**: Application health status

### Database Health

```http
GET /api/v1/health/database
```

**Response**: Database connection status

## Example Endpoints

### Redis Examples

```http
GET /api/v1/redis-example/health
```

**Response**: Redis connection status and info

```http
POST /api/v1/redis-example/cache
Content-Type: application/json

{
  "key": "string",
  "value": "any",
  "ttl": number
}
```

**Response**: Cache operation result

### Database Examples

```http
GET /api/v1/database-example/accounts
```

**Response**: List of accounts (example endpoint)

## Response Formats

### Success Response (Standard)

```json
{
  "result": "success",
  "data": {
    "access_token": "jwt_token_here",
    "refresh_token": "jwt_token_here",
    "token_type": "Bearer",
    "expires_in": 3600,
    "refresh_expires_in": 2592000
  }
}
```

### Error Response

```json
{
  "detail": "Error message",
  "status_code": 400
}
```

### User Profile Response

```json
{
  "id": "uuid",
  "name": "string",
  "email": "string",
  "status": "ACTIVE|PENDING|BANNED|CLOSED",
  "timezone": "string",
  "avatar": "string|null",
  "is_admin": boolean,
  "last_login_at": "datetime|null",
  "initialized_at": "datetime|null",
  "created_at": "datetime"
}
```

## Authentication

### Bearer Token

Include access token in Authorization header:

```http
Authorization: Bearer <access_token>
```

### Alternative Headers

```http
X-Access-Token: <access_token>
X-Session-ID: <session_id>
```

## Status Codes

- **200**: Success
- **400**: Bad Request (validation error, account status issue)
- **401**: Unauthorized (invalid credentials, expired token)
- **403**: Forbidden (insufficient permissions)
- **422**: Unprocessable Entity (input validation error)
- **500**: Internal Server Error
- **503**: Service Unavailable (database/redis unavailable)

## Rate Limiting

Currently no rate limiting implemented. Consider implementing for production:

- Login attempts: 5 per minute per IP
- Registration: 3 per hour per IP
- Token refresh: 10 per minute per user

## CORS

CORS is configured to allow:

- Origins: Configurable via environment
- Methods: GET, POST, PUT, DELETE, OPTIONS
- Headers: Authorization, Content-Type, X-Access-Token

## Security Headers

The following security headers are automatically added:

- `X-Content-Type-Options: nosniff`
- `X-Frame-Options: DENY`
- `X-XSS-Protection: 1; mode=block`
- `Strict-Transport-Security: max-age=31536000; includeSubDomains`
- `Content-Security-Policy: default-src 'self'`

## Environment Configuration

Required environment variables:

```bash
# Database
DATABASE_URL=postgresql://user:password@localhost:5432/madcrow

# JWT Secret
SECRET_KEY=your-secret-key-here

# Redis (optional)
REDIS_URL=redis://localhost:6379/0

# Application
DEBUG=false
DEPLOY_ENV=production
```

## Testing

### Health Check

```bash
curl http://localhost:8000/api/v1/health
```

### Register User

```bash
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"name":"Test User","email":"test@example.com","password":"SecurePass123!"}'
```

### Login

```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"SecurePass123!"}'
```

### Access Protected Endpoint

```bash
curl -X GET http://localhost:8000/api/v1/auth/me \
  -H "Authorization: Bearer <access_token>"
```

## OpenAPI Documentation

Interactive API documentation is available at:

- **Swagger UI**: `http://localhost:8000/docs` (debug mode only)
- **ReDoc**: `http://localhost:8000/redoc` (debug mode only)

In production, these endpoints are disabled for security.

## SDK Examples

### JavaScript/TypeScript

```typescript
class MadcrowAPI {
  private baseURL: string;
  private accessToken: string | null = null;

  constructor(baseURL: string) {
    this.baseURL = baseURL;
  }

  async login(email: string, password: string): Promise<TokenPair> {
    const response = await fetch(`${this.baseURL}/api/v1/auth/login`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, password, remember_me: false }),
    });

    const { result, data } = await response.json();
    if (result === "success") {
      this.accessToken = data.access_token;
      return data;
    }
    throw new Error("Login failed");
  }

  async getCurrentUser(): Promise<UserProfile> {
    const response = await fetch(`${this.baseURL}/api/v1/auth/me`, {
      headers: { Authorization: `Bearer ${this.accessToken}` },
    });

    if (!response.ok) {
      throw new Error("Failed to get current user");
    }

    return response.json();
  }
}
```

### Python

```python
import requests
from typing import Dict, Any

class MadcrowAPI:
    def __init__(self, base_url: str):
        self.base_url = base_url
        self.access_token = None

    def login(self, email: str, password: str) -> Dict[str, Any]:
        response = requests.post(
            f"{self.base_url}/api/v1/auth/login",
            json={"email": email, "password": password, "remember_me": False}
        )
        response.raise_for_status()

        data = response.json()
        if data["result"] == "success":
            self.access_token = data["data"]["access_token"]
            return data["data"]

        raise Exception("Login failed")

    def get_current_user(self) -> Dict[str, Any]:
        response = requests.get(
            f"{self.base_url}/api/v1/auth/me",
            headers={"Authorization": f"Bearer {self.access_token}"}
        )
        response.raise_for_status()
        return response.json()
```

For detailed implementation guides, see the [Authentication System documentation](./authentication.md).

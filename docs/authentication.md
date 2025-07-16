# Authentication System

This document describes the secure authentication system implemented in the Madcrow backend, including user registration, login, and JWT token management.

## Overview

The authentication system provides secure, modern authentication with:

- **User Registration** with password strength validation
- **JWT-based Authentication** with access and refresh tokens
- **Secure Password Hashing** using SHA-256 + salt
- **Session Management** with Redis integration
- **Admin User Creation** via command line

## Architecture

### Password Security

The system uses secure password hashing:

- **Algorithm**: SHA-256 with base64-encoded salt
- **Storage**: Separate `password` and `password_salt` fields
- **Validation**: Comprehensive password strength requirements

### Token System

- **Access Token**: JWT with 1-hour expiration for API access
- **Refresh Token**: JWT with 30-day expiration for token renewal
- **Token Type**: Bearer tokens in Authorization header

### Database Schema

```sql
-- Account table fields
id              UUID PRIMARY KEY
name            VARCHAR(255) NOT NULL
email           VARCHAR(255) UNIQUE NOT NULL
password        VARCHAR(255)         -- SHA-256 hash
password_salt   VARCHAR(255)         -- Base64 salt
status          VARCHAR(50)          -- ACTIVE, PENDING, BANNED, CLOSED
is_admin        BOOLEAN DEFAULT FALSE
timezone        VARCHAR(50)
avatar          VARCHAR(500)
last_login_at   TIMESTAMP
last_login_ip   VARCHAR(45)
initialized_at  TIMESTAMP
created_at      TIMESTAMP
updated_at      TIMESTAMP
is_deleted      BOOLEAN DEFAULT FALSE
```

## API Endpoints

### User Registration

**Endpoint**: `POST /api/v1/auth/register`

**Request**:

```json
{
  "name": "John Doe",
  "email": "john.doe@example.com",
  "password": "SecurePassword123!"
}
```

**Response** (Success - 200):

```json
{
  "result": "success",
  "data": {
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "token_type": "Bearer",
    "expires_in": 3600,
    "refresh_expires_in": 2592000
  }
}
```

**Error Responses**:

- `400`: Password validation failed or email already exists
- `422`: Invalid input format
- `500`: Server error

### User Login

**Endpoint**: `POST /api/v1/auth/login`

**Request**:

```json
{
  "email": "john.doe@example.com",
  "password": "SecurePassword123!",
  "remember_me": false
}
```

**Response** (Success - 200):

```json
{
  "result": "success",
  "data": {
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "token_type": "Bearer",
    "expires_in": 3600,
    "refresh_expires_in": 2592000
  }
}
```

**Error Responses**:

- `401`: Invalid credentials
- `400`: Account not active (pending, banned, closed)
- `422`: Invalid input format

### Token Refresh

**Endpoint**: `POST /api/v1/auth/refresh-token`

**Request**:

```json
{
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**Response** (Success - 200):

```json
{
  "result": "success",
  "data": {
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "token_type": "Bearer",
    "expires_in": 3600,
    "refresh_expires_in": 2592000
  }
}
```

**Error Responses**:

- `401`: Invalid or expired refresh token

### Get Current User

**Endpoint**: `GET /api/v1/auth/me`

**Headers**:

```
Authorization: Bearer <access_token>
```

**Response** (Success - 200):

```json
{
  "id": "123e4567-e89b-12d3-a456-426614174000",
  "name": "John Doe",
  "email": "john.doe@example.com",
  "status": "ACTIVE",
  "timezone": "UTC",
  "avatar": null,
  "is_admin": false,
  "last_login_at": "2024-01-15T10:30:00Z",
  "initialized_at": "2024-01-01T00:00:00Z",
  "created_at": "2024-01-01T00:00:00Z"
}
```

### Session Validation

**Endpoint**: `GET /api/v1/auth/session/validate`

**Headers**:

```
Authorization: Bearer <access_token>
```

**Response** (Success - 200):

```json
{
  "valid": true,
  "user": {
    "id": "123e4567-e89b-12d3-a456-426614174000",
    "name": "John Doe",
    "email": "john.doe@example.com",
    "status": "ACTIVE",
    "is_admin": false
  },
  "session": {
    "session_id": "sess_123e4567e89b12d3a456426614174000",
    "expires_at": "2024-01-16T10:30:00Z",
    "remember_me": false
  },
  "message": "Session is valid"
}
```

### Logout

**Endpoint**: `POST /api/v1/auth/logout`

**Headers**:

```
Authorization: Bearer <access_token>
```

**Request**:

```json
{
  "session_id": "optional_session_id"
}
```

**Response** (Success - 200):

```json
{
  "success": true,
  "message": "Logout successful",
  "logged_out_at": "2024-01-15T11:00:00Z"
}
```

### Logout All Sessions

**Endpoint**: `POST /api/v1/auth/logout-all`

**Headers**:

```
Authorization: Bearer <access_token>
```

**Response** (Success - 200):

```json
{
  "success": true,
  "message": "Logged out from 3 sessions",
  "sessions_deleted": 3,
  "logged_out_at": "2024-01-15T11:00:00Z"
}
```

## Password Requirements

The system enforces the following password requirements:

- **Minimum Length**: 8 characters
- **Maximum Length**: 128 characters
- **Required Characters**: At least one letter and one digit
- **Forbidden**: Common weak passwords (password, 123456, etc.)

## Authentication Headers

### Bearer Token Authentication

Include the access token in the Authorization header:

```
Authorization: Bearer <access_token>
```

### Alternative Headers

The system also accepts tokens via:

- `X-Access-Token`: Direct token header
- `X-Session-ID`: Session-based authentication (legacy)

## Error Handling

### Standard Error Response

```json
{
  "result": "error",
  "message": "Error description",
  "code": "ERROR_CODE"
}
```

### Common Error Codes

- `INVALID_CREDENTIALS`: Wrong email or password
- `ACCOUNT_PENDING`: Account not activated
- `ACCOUNT_BANNED`: Account suspended
- `ACCOUNT_CLOSED`: Account closed
- `WEAK_PASSWORD`: Password doesn't meet requirements
- `EMAIL_EXISTS`: Email already registered
- `TOKEN_EXPIRED`: Access token expired
- `TOKEN_INVALID`: Malformed or invalid token

## Account Status

- **ACTIVE**: Normal account, can login
- **PENDING**: Account created but not activated
- **BANNED**: Account suspended by admin
- **CLOSED**: Account permanently closed

## Admin User Creation

Create admin users via command line:

```bash
# Interactive mode
uv run python command.py create-admin

# With parameters
uv run python command.py create-admin --email admin@example.com --name "Admin User"
```

The command will:

1. Prompt for secure password input
2. Validate password strength
3. Create account with admin privileges
4. Use secure password hashing

## Security Features

### Password Security

- SHA-256 hashing with unique salt per password
- Base64-encoded salt storage
- Password strength validation
- Protection against common weak passwords

### Token Security

- JWT tokens with expiration
- Separate access and refresh tokens
- Token revocation support (planned)
- Secure token storage recommendations

### Session Security

- Redis-based session storage
- Session expiration and cleanup
- IP address tracking
- Multi-session management

## Integration Examples

### Frontend Integration

```javascript
// Login
const loginResponse = await fetch("/api/v1/auth/login", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({
    email: "user@example.com",
    password: "password123",
    remember_me: false,
  }),
});

const { result, data } = await loginResponse.json();
if (result === "success") {
  localStorage.setItem("access_token", data.access_token);
  localStorage.setItem("refresh_token", data.refresh_token);
}

// Authenticated API calls
const apiResponse = await fetch("/api/v1/auth/me", {
  headers: {
    Authorization: `Bearer ${localStorage.getItem("access_token")}`,
  },
});
```

### Token Refresh Flow

```javascript
// Automatic token refresh
async function refreshToken() {
  const refreshToken = localStorage.getItem("refresh_token");
  const response = await fetch("/api/v1/auth/refresh-token", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ refresh_token: refreshToken }),
  });

  const { result, data } = await response.json();
  if (result === "success") {
    localStorage.setItem("access_token", data.access_token);
    localStorage.setItem("refresh_token", data.refresh_token);
    return data.access_token;
  }

  // Redirect to login
  window.location.href = "/login";
}
```

## Configuration

### Environment Variables

```bash
# Required for JWT tokens
SECRET_KEY=your-secret-key-here

# Database configuration
DATABASE_URL=postgresql://user:password@localhost:5432/madcrow

# Redis configuration (for sessions)
REDIS_URL=redis://localhost:6379/0
```

### Token Configuration

Default token expiration times:

- Access Token: 1 hour (3600 seconds)
- Refresh Token: 30 days (2592000 seconds)

These can be configured in `src/services/token_service.py`.

## Troubleshooting

### Common Issues

1. **503 Service Unavailable**: Database or Redis not running
2. **401 Unauthorized**: Invalid or expired token
3. **400 Bad Request**: Password validation failed
4. **422 Unprocessable Entity**: Invalid input format

### Debug Mode

Enable debug logging to see detailed authentication flow:

```bash
export LOG_LEVEL=DEBUG
```

### Health Checks

Check authentication system health:

- Database connectivity: Ensure PostgreSQL is running
- Redis connectivity: Ensure Redis is running (for sessions)
- Token validation: Test with known good tokens

## Migration from bcrypt

If migrating from the old bcrypt-based system:

1. **Database Migration**: Add `password` and `password_salt` fields
2. **User Migration**: Users need to reset passwords or re-register
3. **Admin Recreation**: Use updated `create-admin` command
4. **Code Updates**: Update any direct password handling code

The new system is not backward compatible with bcrypt hashes due to the different hashing algorithm and storage format.

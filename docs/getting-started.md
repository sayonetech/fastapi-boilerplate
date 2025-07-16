# Getting Started with Madcrow Backend

This guide will help you get up and running with the Madcrow Backend authentication system quickly.

## Prerequisites

- Python 3.12+
- PostgreSQL database
- Redis server (optional, for sessions)
- uv package manager

## Quick Setup

### 1. Environment Setup

```bash
# Clone and setup
git clone <repository-url>
cd madcrow-backend

# Install dependencies
uv sync

# Copy environment file
cp .env.example .env
```

### 2. Configure Environment

Edit `.env` file:

```bash
# Database
DATABASE_URL=postgresql://user:password@localhost:5432/madcrow

# JWT Secret (generate a secure key)
SECRET_KEY=your-very-secure-secret-key-here

# Optional: Redis for sessions
REDIS_URL=redis://localhost:6379/0

# Application
DEBUG=true
DEPLOY_ENV=development
```

### 3. Database Setup

```bash
# Start PostgreSQL (using Docker)
docker run --name postgres -e POSTGRES_PASSWORD=password -p 5432:5432 -d postgres

# Run migrations
uv run alembic upgrade head
```

### 4. Create Admin User

```bash
# Create admin user
uv run python command.py create-admin

# Follow prompts:
# - Email: admin@example.com
# - Name: Admin User
# - Password: SecureAdminPass123!
```

For more CLI commands and options, see the [Commands Documentation](./commands.md).

### 5. Start Application

```bash
# Start the server
uv run python main.py

# Server will start at http://localhost:8000
```

## First API Calls

### 1. Health Check

```bash
curl http://localhost:8000/api/v1/health
```

Expected response:

```json
{
  "status": "healthy",
  "timestamp": "2024-01-15T10:30:00Z",
  "version": "1.0.0"
}
```

### 2. Register New User

```bash
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "name": "John Doe",
    "email": "john@example.com",
    "password": "SecurePassword123!"
  }'
```

Expected response:

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

### 3. Login with Admin

```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@example.com",
    "password": "SecureAdminPass123!",
    "remember_me": false
  }'
```

### 4. Access Protected Endpoint

```bash
# Use the access_token from login/register response
curl -X GET http://localhost:8000/api/v1/auth/me \
  -H "Authorization: Bearer <your_access_token>"
```

Expected response:

```json
{
  "id": "123e4567-e89b-12d3-a456-426614174000",
  "name": "John Doe",
  "email": "john@example.com",
  "status": "ACTIVE",
  "timezone": "UTC",
  "avatar": null,
  "is_admin": false,
  "last_login_at": "2024-01-15T10:30:00Z",
  "created_at": "2024-01-15T10:00:00Z"
}
```

## Key Features

### Authentication System

- **Secure Hashing**: Uses secure password hashing (SHA-256 + salt)
- **JWT Tokens**: Access tokens (1h) and refresh tokens (30d)
- **Password Security**: Strong password requirements and validation
- **Account Management**: User registration, login, logout

### API Design

- **RESTful**: Clean REST API design
- **Type Safety**: Full Pydantic validation and mypy compliance
- **Error Handling**: Comprehensive error responses
- **Documentation**: Auto-generated OpenAPI docs (debug mode)

### Security Features

- **Password Hashing**: SHA-256 with unique salt per password
- **JWT Security**: Signed tokens with expiration
- **Security Headers**: Comprehensive security headers middleware
- **Input Validation**: Strong input validation and sanitization

### Development Features

- **Class-Based Views**: Clean FastAPI CBV implementation
- **Error Factory**: Consistent error handling across the app
- **Redis Integration**: Caching and session management
- **Database Migrations**: Alembic-based database versioning

## Development Workflow

### 1. Adding New Endpoints

```python
# src/routes/v1/my_feature.py
from ..base_router import BaseRouter
from ..cbv import cbv, get, post

my_router = BaseRouter(prefix="/v1/my-feature", tags=["my-feature"])

@cbv(my_router)
class MyFeatureController:
    @get("/items")
    async def get_items(self) -> List[Item]:
        return []

    @post("/items")
    async def create_item(self, item: CreateItemRequest) -> Item:
        return item
```

### 2. Adding Authentication

```python
from ...dependencies.auth import CurrentUser

@cbv(my_router)
class MyFeatureController:
    @get("/protected")
    async def protected_endpoint(self, current_user: CurrentUser) -> dict:
        return {"user": current_user.email}
```

### 3. Database Models

```python
# src/entities/my_model.py
from sqlmodel import SQLModel, Field
from uuid import UUID, uuid4

class MyModel(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    name: str = Field(max_length=255)
    created_at: datetime = Field(default_factory=datetime.utcnow)
```

### 4. Running Tests

```bash
# Run all tests
uv run pytest

# Run specific test file
uv run pytest tests/test_auth.py

# Run with coverage
uv run pytest --cov=src
```

## Common Issues

### Database Connection Error

```
sqlalchemy.exc.OperationalError: could not connect to server
```

**Solution**: Ensure PostgreSQL is running and DATABASE_URL is correct.

### JWT Secret Key Error

```
ValueError: SECRET_KEY must be configured for JWT tokens
```

**Solution**: Set SECRET_KEY in your .env file.

### Redis Connection Error (503)

```
503 Service Unavailable
```

**Solution**: Start Redis server or disable Redis-dependent features.

### Password Validation Error

```
Password validation failed: Password must be at least 8 characters long
```

**Solution**: Use a stronger password meeting the requirements:

- Minimum 8 characters
- At least one letter
- At least one digit

## Next Steps

1. **Read Documentation**: Check out the [Authentication System](./authentication.md) guide
2. **API Reference**: Review the [API Reference](./api-reference.md) for all endpoints
3. **Production Setup**: Follow the [Production Checklist](./PRODUCTION_CHECKLIST.md)
4. **Security**: Configure [Security Headers](./SECURITY_HEADERS.md)
5. **Development**: Learn about [Class-Based Views](./CBV_README.md)

## Support

- **Documentation**: Check the `docs/` directory for detailed guides
- **Issues**: Report issues in the project repository
- **Development**: Follow the development patterns in existing code

## Example Frontend Integration

### React/TypeScript Example

```typescript
// api/auth.ts
export class AuthAPI {
  private baseURL = "http://localhost:8000";

  async register(name: string, email: string, password: string) {
    const response = await fetch(`${this.baseURL}/api/v1/auth/register`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ name, email, password }),
    });

    const data = await response.json();
    if (data.result === "success") {
      localStorage.setItem("access_token", data.data.access_token);
      localStorage.setItem("refresh_token", data.data.refresh_token);
      return data.data;
    }

    throw new Error(data.message || "Registration failed");
  }

  async login(email: string, password: string) {
    const response = await fetch(`${this.baseURL}/api/v1/auth/login`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, password, remember_me: false }),
    });

    const data = await response.json();
    if (data.result === "success") {
      localStorage.setItem("access_token", data.data.access_token);
      localStorage.setItem("refresh_token", data.data.refresh_token);
      return data.data;
    }

    throw new Error("Login failed");
  }

  async getCurrentUser() {
    const token = localStorage.getItem("access_token");
    const response = await fetch(`${this.baseURL}/api/v1/auth/me`, {
      headers: { Authorization: `Bearer ${token}` },
    });

    if (!response.ok) {
      throw new Error("Failed to get user");
    }

    return response.json();
  }
}
```

This should get you started with the Madcrow Backend! For more detailed information, check out the specific documentation files in the `docs/` directory.

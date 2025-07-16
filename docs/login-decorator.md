# Login Required Decorator

This document describes the `@login_required` and `@admin_required` decorators that provide an alternative to FastAPI's dependency injection for authentication.

## Overview

The login decorators follow the pattern from Dify's authentication system but are adapted for FastAPI. They provide a simple way to ensure endpoints require authentication without using dependency injection.

## Available Decorators

### `@login_required`

Ensures the user is authenticated before accessing the endpoint.

```python
from src.libs.login import login_required

@login_required
async def my_endpoint(request: Request) -> dict:
    # User is guaranteed to be authenticated here
    return {"message": "success"}
```

### `@admin_required`

Ensures the user is authenticated AND has admin privileges.

```python
from src.libs.login import admin_required

@admin_required
async def admin_endpoint(request: Request) -> dict:
    # User is guaranteed to be authenticated and admin here
    return {"message": "admin access granted"}
```

## Usage Examples

### Basic Authentication

```python
from fastapi import Request
from src.libs.login import login_required

@cbv(router)
class MyController:
    @get("/protected")
    @login_required
    async def protected_endpoint(self, request: Request) -> dict:
        # At this point, user is authenticated
        # You can get user info if needed:
        from src.dependencies.auth import get_current_user_from_jwt
        from src.dependencies.db import get_session

        db_session = next(get_session())
        try:
            current_user = get_current_user_from_jwt(request, db_session)
            return {"user_email": current_user.email}
        finally:
            db_session.close()
```

### Admin-Only Endpoint

```python
@cbv(router)
class AdminController:
    @post("/admin-action")
    @admin_required
    async def admin_action(self, request: Request) -> dict:
        # User is authenticated and has admin privileges
        return {"message": "Admin action completed"}
```

## Comparison with Dependency Injection

### Using Dependency Injection (Recommended)

```python
from src.dependencies.auth import CurrentUser

@cbv(router)
class MyController:
    @get("/profile")
    async def get_profile(self, current_user: CurrentUser) -> UserProfile:
        # User automatically injected and validated
        return current_user
```

### Using Login Decorator (Alternative)

```python
from src.libs.login import login_required

@cbv(router)
class MyController:
    @get("/profile-alt")
    @login_required
    async def get_profile_alt(self, request: Request) -> dict:
        # Must manually extract user from request
        # More verbose but follows Dify pattern
        return {"message": "authenticated"}
```

## When to Use Each Approach

### Use Dependency Injection (`CurrentUser`) When:

- You need the user object in your endpoint
- You want automatic validation and injection
- You prefer FastAPI's standard patterns
- You want cleaner, more readable code

### Use Login Decorator When:

- You want to follow Dify's authentication pattern
- You need simple authentication without user injection
- You're migrating from Flask-Login patterns
- You want explicit decorator-based authentication

## Configuration

### Testing Mode

You can disable authentication for testing by setting:

```bash
LOGIN_DISABLED=true
```

**WARNING**: Only use this in development/testing environments!

### Environment Variables

```bash
# Disable login requirements (testing only)
LOGIN_DISABLED=false

# Required for JWT validation
SECRET_KEY=your-secret-key-here
```

## Error Handling

The decorators will raise appropriate HTTP exceptions:

- **401 Unauthorized**: Invalid or missing token
- **403 Forbidden**: Valid user but insufficient privileges (admin_required only)
- **500 Internal Server Error**: Authentication service errors

## Implementation Details

### Authentication Flow

1. **Extract Request**: Decorator finds the `Request` object in function arguments
2. **Check Configuration**: Skip authentication if `LOGIN_DISABLED=true`
3. **Validate Token**: Extract and verify JWT token from headers
4. **Check User Status**: Ensure user exists and is active
5. **Admin Check**: For `@admin_required`, verify admin privileges
6. **Call Function**: Execute the original endpoint function

### Token Sources

The decorator checks for tokens in:

1. `Authorization: Bearer <token>` header
2. `X-Access-Token: <token>` header

### Database Sessions

The decorator manages database sessions automatically:

- Opens session for user validation
- Closes session after validation
- Handles connection errors gracefully

## Best Practices

1. **Always include Request parameter** when using decorators:

   ```python
   @login_required
   async def my_endpoint(self, request: Request) -> dict:
       # Request is required for token extraction
   ```

2. **Use dependency injection for user data**:

   ```python
   # Preferred approach
   async def endpoint(self, current_user: CurrentUser) -> dict:
       return {"user": current_user.email}
   ```

3. **Handle errors appropriately**:

   ```python
   @login_required
   async def endpoint(self, request: Request) -> dict:
       try:
           # Your logic here
           return {"success": True}
       except Exception as e:
           logger.exception("Error in endpoint")
           raise HTTPException(status_code=500, detail="Internal error")
   ```

4. **Don't mix patterns unnecessarily**:
   ```python
   # Avoid this - redundant authentication
   @login_required
   async def endpoint(self, request: Request, current_user: CurrentUser) -> dict:
       # Both decorator and dependency do authentication
   ```

## Troubleshooting

### Common Issues

1. **"Request object not found"**: Ensure your endpoint has a `Request` parameter
2. **"Authentication service error"**: Check database connectivity
3. **"Invalid token"**: Verify JWT token format and SECRET_KEY configuration

### Debug Logging

Enable debug logging to see authentication flow:

```python
import logging
logging.getLogger("src.libs.login").setLevel(logging.DEBUG)
```

## Migration from Flask-Login

If migrating from Flask-Login patterns:

```python
# Flask-Login pattern
@login_required
def my_view():
    user = current_user
    return {"user": user.email}

# FastAPI equivalent
@login_required
async def my_view(request: Request):
    # Manual user extraction needed
    current_user = get_current_user_from_jwt(request, db_session)
    return {"user": current_user.email}
```

The FastAPI dependency injection approach is generally preferred:

```python
# FastAPI recommended pattern
async def my_view(current_user: CurrentUser):
    return {"user": current_user.email}
```

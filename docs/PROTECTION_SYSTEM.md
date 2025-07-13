# Class-Level Protection System

The protection system provides a comprehensive solution for enforcing authentication at both the controller (class) and method levels, offering centralized protection management through middleware.

## Overview

The system consists of four main components:

1. **Protection Annotations** - Declarative way to specify protection requirements
2. **Enhanced CBV Integration** - Automatic route-controller mapping
3. **Protection Middleware** - Centralized authentication enforcement
4. **Compatibility Layer** - Works with existing `@login_required` decorators

## Features

- ✅ **Class-level protection** - Protect entire controllers with a single flag
- ✅ **Method-level overrides** - Fine-grained control per endpoint
- ✅ **Middleware enforcement** - Centralized authentication logic
- ✅ **Backward compatibility** - Works with existing decorators
- ✅ **Route mapping** - Automatic controller-route association
- ✅ **Flexible configuration** - Multiple ways to configure protection

## Usage Patterns

### 1. Class-Level Protection (Inheritance)

```python
from ..protection import ProtectedController

@cbv(router)
class UserController(ProtectedController):
    """All methods require authentication by default."""

    protected = True  # Class-level protection

    @get("/profile")
    async def get_profile(self, current_user: CurrentUser):
        # Protected by class-level setting
        return {"user": current_user.email}

    @get("/public-info")
    @no_protection  # Override class protection
    async def get_public_info(self):
        # This method is public despite class protection
        return {"info": "public"}
```

### 2. Class-Level Protection (Decorator)

```python
from ..protection import protected_controller

@protected_controller(protected=True)
@cbv(router)
class AdminController:
    """All methods require authentication."""

    @get("/dashboard")
    async def dashboard(self, current_user: CurrentUser):
        # Protected by class-level decorator
        return {"dashboard": "data"}

    @get("/status")
    @no_protection  # Override protection
    async def public_status(self):
        # Public endpoint
        return {"status": "ok"}
```

### 3. Mixed Protection

```python
@cbv(router)
class MixedController:
    """Controller with mixed protection levels."""

    @get("/public")
    async def public_endpoint(self):
        # No protection required
        return {"message": "public"}

    @get("/private")
    @require_protection  # Method-level protection
    async def private_endpoint(self, current_user: CurrentUser):
        # Protected by method decorator
        return {"user": current_user.email}

    @get("/legacy")
    @login_required  # Traditional decorator
    async def legacy_endpoint(self, request: Request):
        # Protected by login_required decorator
        return {"message": "legacy protected"}
```

## Protection Decorators

### Class-Level Decorators

#### `@protected_controller(protected=True)`

Marks an entire controller as protected.

```python
@protected_controller(protected=True)
@cbv(router)
class ProtectedController:
    # All methods require authentication
    pass
```

#### `ProtectedController` Base Class

Alternative to decorator approach.

```python
@cbv(router)
class MyController(ProtectedController):
    protected = True  # Enable class-level protection
```

### Method-Level Decorators

#### `@no_protection`

Explicitly disables protection for a method.

```python
@get("/public")
@no_protection
async def public_method(self):
    return {"message": "public"}
```

#### `@require_protection`

Explicitly requires protection for a method.

```python
@get("/private")
@require_protection
async def private_method(self, current_user: CurrentUser):
    return {"user": current_user.email}
```

#### `@login_required` (Legacy)

Traditional method-level protection.

```python
@get("/legacy")
@login_required
async def legacy_method(self, request: Request):
    return {"message": "protected"}
```

## Middleware Configuration

The protection middleware is automatically configured and handles:

- Route-controller mapping resolution
- Authentication enforcement
- Excluded paths (docs, health checks, etc.)
- Error handling and logging

### Default Excluded Paths

```python
excluded_paths = [
    "/docs",
    "/redoc",
    "/openapi.json",
    "/favicon.ico",
    "/health",
    "/api/v1/health",
    "/api/v1/security/info",
]
```

### Custom Configuration

```python
# In extension configuration
custom_middleware = create_protection_middleware(
    exclude_paths=["/custom/public", "/api/v1/status"]
)
```

## How It Works

### 1. Route Registration

When controllers are registered with `@cbv()`:

```python
@cbv(router)
class MyController(ProtectedController):
    protected = True

    @get("/endpoint")
    async def my_method(self): ...
```

The system automatically:

- Maps routes to controller classes and methods
- Stores protection metadata
- Registers route-controller associations

### 2. Request Processing

When a request comes in:

```python
# Middleware checks:
1. Is path excluded? → Skip protection
2. Does route require protection? → Check controller/method settings
3. Is authentication required? → Enforce via existing auth system
4. Continue to endpoint handler
```

### 3. Protection Resolution

Protection is resolved in this order:

1. **Method-level override** (`@no_protection`, `@require_protection`)
2. **Legacy decorator** (`@login_required`)
3. **Class-level setting** (`protected = True`)
4. **Default** (no protection)

## Integration with Existing System

### CurrentUser Dependency

Works seamlessly with existing dependency injection:

```python
@get("/profile")
async def get_profile(self, current_user: CurrentUser):
    # current_user is injected as usual
    return {"user": current_user.email}
```

### Request State

Middleware sets authenticated user in request state:

```python
@get("/conditional")
async def conditional_endpoint(self, request: Request):
    # User set by middleware (if authenticated)
    user = getattr(request.state, "current_user", None)
    if user:
        return {"user": user.email}
    else:
        return {"message": "anonymous"}
```

## Configuration Options

### Environment Variables

```bash
# Disable login for testing
LOGIN_DISABLED=true

# Debug mode for detailed logging
DEBUG=true
```

### Class-Level Settings

```python
class MyController(ProtectedController):
    protected = True  # Require authentication for all methods
```

### Method-Level Settings

```python
@get("/endpoint")
@no_protection  # Override class protection
async def public_method(self): ...

@get("/secure")
@require_protection  # Force protection
async def secure_method(self, current_user: CurrentUser): ...
```

## Monitoring and Debugging

### Protection Status Endpoint

```bash
GET /api/v1/example-protection/status
```

Returns:

```json
{
  "message": "Protection system status",
  "status": {
    "extension_active": true,
    "protected_routes_count": 15,
    "protected_routes": {
      "GET:/api/v1/profile/me": {
        "controller": "ProfileController",
        "method": "get_current_user"
      }
    }
  }
}
```

### Debug Logging

Enable debug logging to see protection decisions:

```python
# In logs you'll see:
DEBUG [protection_middleware.py] Route GET /api/v1/profile/me protection required: True
DEBUG [protection_middleware.py] Authentication successful for user: user@example.com
```

## Migration Guide

### From Function-Based to Class-Based Protection

**Before:**

```python
@router.get("/users")
@login_required
async def get_users(request: Request): ...

@router.post("/users")
@login_required
async def create_user(request: Request): ...
```

**After:**

```python
@cbv(router)
class UserController(ProtectedController):
    protected = True  # Protect all methods

    @get("/users")
    async def get_users(self, current_user: CurrentUser): ...

    @post("/users")
    async def create_user(self, current_user: CurrentUser): ...
```

### Gradual Migration

You can migrate gradually by mixing approaches:

```python
@cbv(router)
class UserController:
    @get("/users")
    @login_required  # Keep existing decorator
    async def get_users(self, request: Request): ...

    @post("/users")
    @require_protection  # Use new decorator
    async def create_user(self, current_user: CurrentUser): ...
```

## Best Practices

1. **Use class-level protection** for controllers that are mostly protected
2. **Use method-level overrides** for exceptions (public endpoints in protected controllers)
3. **Use CurrentUser dependency** instead of manual request parsing
4. **Test protection** using the status endpoint
5. **Monitor logs** in debug mode to verify protection behavior
6. **Exclude appropriate paths** from protection (health checks, docs)

## Troubleshooting

### Common Issues

**Routes not being protected:**

- Check if controller is properly registered with `@cbv()`
- Verify protection flags are set correctly
- Check middleware is initialized in extensions

**Authentication errors:**

- Ensure JWT tokens are properly formatted
- Check database connectivity
- Verify user accounts are active

**Performance concerns:**

- Middleware adds minimal overhead
- Route mapping is cached
- Authentication is only performed when required

### Debug Steps

1. Check protection status endpoint
2. Enable debug logging
3. Verify route registration in logs
4. Test with `LOGIN_DISABLED=true`

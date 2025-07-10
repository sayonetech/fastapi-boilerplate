# Class-Based Views (CBV) for FastAPI

This document describes the custom Class-Based Views implementation for FastAPI routers in the Madcrow Backend project.

## Overview

Class-Based Views (CBV) provide a way to organize related route handlers into classes, making code more maintainable and following object-oriented principles. This implementation is compatible with Pydantic v2 and modern FastAPI versions.

## Why Class-Based Views?

### Benefits
- **Organization**: Group related endpoints in a single class
- **Code Reuse**: Share common logic between methods
- **Maintainability**: Easier to manage complex controllers
- **Dependency Injection**: Full FastAPI dependency injection support
- **Type Safety**: Complete type hints and IDE support

### Comparison with Function-Based Views

**Function-Based (Traditional)**:
```python
@router.get("/users")
async def get_users(): ...

@router.post("/users")
async def create_user(): ...

@router.get("/users/{user_id}")
async def get_user(): ...
```

**Class-Based (Our Implementation)**:
```python
@cbv(router)
class UserController:
    @get("/users")
    async def get_users(self): ...
    
    @post("/users")
    async def create_user(self): ...
    
    @get("/users/{user_id}")
    async def get_user(self): ...
```

## Implementation

### Core Components

1. **CBV Decorator**: `@cbv(router)` - Converts a class to class-based views
2. **Route Decorators**: `@get`, `@post`, `@put`, `@patch`, `@delete` - Mark methods as routes
3. **BaseRouter**: Custom router with automatic API prefix

## Usage Guide

### Basic Example

```python
from fastapi import HTTPException, status
from ..base_router import BaseRouter
from ..cbv import cbv, get, post

# Create router
router = BaseRouter(prefix="/v1/users", tags=["users"])

@cbv(router)
class UserController:
    """User management controller."""
    
    @get("/", response_model=List[UserResponse])
    async def list_users(self) -> List[UserResponse]:
        """Get all users."""
        return await get_all_users()
    
    @post("/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
    async def create_user(self, user_data: CreateUserRequest) -> UserResponse:
        """Create a new user."""
        return await create_new_user(user_data)
```

### With Dependency Injection

```python
from ..services.user_service import UserServiceDep

@cbv(router)
class UserController:
    @get("/{user_id}")
    async def get_user(
        self,
        user_id: UUID,
        user_service: UserServiceDep,
    ) -> UserResponse:
        """Get user by ID."""
        user = await user_service.get_by_id(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        return user
```

### All HTTP Methods

```python
@cbv(router)
class ResourceController:
    @get("/")
    async def list_resources(self): ...
    
    @post("/")
    async def create_resource(self): ...
    
    @get("/{resource_id}")
    async def get_resource(self): ...
    
    @put("/{resource_id}")
    async def update_resource(self): ...
    
    @patch("/{resource_id}")
    async def partial_update_resource(self): ...
    
    @delete("/{resource_id}")
    async def delete_resource(self): ...
```

### Advanced Features

#### Custom Route Parameters

```python
@cbv(router)
class AdvancedController:
    @get(
        "/search",
        response_model=SearchResponse,
        summary="Search resources",
        description="Advanced search with filters",
        response_description="Search results with pagination"
    )
    async def search(
        self,
        query: str,
        limit: int = 10,
        offset: int = 0
    ) -> SearchResponse:
        """Advanced search endpoint."""
        return await perform_search(query, limit, offset)
```

#### Shared Class State and Methods

```python
@cbv(router)
class UserController:
    def __init__(self):
        """Initialize controller with shared state."""
        self.default_limit = 20
    
    def _validate_user_data(self, data: dict) -> bool:
        """Private method for validation."""
        return "email" in data and "name" in data
    
    @get("/")
    async def list_users(self, limit: int = None) -> List[UserResponse]:
        """List users with default limit."""
        actual_limit = limit or self.default_limit
        return await get_users(limit=actual_limit)
    
    @post("/")
    async def create_user(self, user_data: CreateUserRequest) -> UserResponse:
        """Create user with validation."""
        if not self._validate_user_data(user_data.dict()):
            raise HTTPException(status_code=400, detail="Invalid user data")
        return await create_user(user_data)
```

## Available Decorators

### Route Decorators

| Decorator | HTTP Method | Usage |
|-----------|-------------|-------|
| `@get(path, **kwargs)` | GET | Read operations |
| `@post(path, **kwargs)` | POST | Create operations |
| `@put(path, **kwargs)` | PUT | Full update operations |
| `@patch(path, **kwargs)` | PATCH | Partial update operations |
| `@delete(path, **kwargs)` | DELETE | Delete operations |

### Generic Route Decorator

```python
@route(path="/custom", methods=["GET", "POST"], **kwargs)
async def custom_endpoint(self): ...
```

## Integration with Existing Code

### Router Registration

The CBV implementation works seamlessly with the existing router auto-discovery:

```python
# src/routes/v1/users.py
from ..base_router import BaseRouter
from ..cbv import cbv, get

user_router = BaseRouter(prefix="/v1/users", tags=["users"])

@cbv(user_router)
class UserController:
    # ... controller methods
```

The router will be automatically discovered and registered by the existing `register_routes()` function.

### File Structure

```
src/routes/
├── __init__.py              # Auto-discovery logic
├── base_router.py           # Custom BaseRouter
├── cbv.py                   # CBV implementation
└── v1/
    ├── __init__.py
    ├── health.py            # Health controller (CBV)
    ├── users.py             # User controller (CBV)
    └── products.py          # Product controller (CBV)
```

## Best Practices

### 1. Controller Naming
- Use descriptive names ending with "Controller"
- Example: `UserController`, `ProductController`, `AuthController`

### 2. Method Organization
- Group related operations in the same controller
- Use consistent naming: `list_`, `get_`, `create_`, `update_`, `delete_`

### 3. Error Handling
```python
@cbv(router)
class UserController:
    @get("/{user_id}")
    async def get_user(self, user_id: UUID) -> UserResponse:
        try:
            return await user_service.get_by_id(user_id)
        except UserNotFoundError:
            raise HTTPException(status_code=404, detail="User not found")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")
```

### 4. Documentation
- Add docstrings to controller classes and methods
- Use FastAPI's automatic documentation features
- Include response models and status codes

### 5. Dependency Injection
- Use typed dependencies for better IDE support
- Keep dependencies at the method level for clarity

## Migration from Function-Based Views

### Step 1: Create Controller Class
```python
# Before
@router.get("/users")
async def get_users(): ...

# After
@cbv(router)
class UserController:
    @get("/users")
    async def get_users(self): ...
```

### Step 2: Add Self Parameter
All methods need `self` as the first parameter.

### Step 3: Update Imports
```python
from ..cbv import cbv, get, post, put, patch, delete
```

### Step 4: Test
Ensure all endpoints work correctly after migration.

## Troubleshooting

### Common Issues

1. **Missing `self` parameter**
   ```python
   # Wrong
   @get("/")
   async def get_items(): ...
   
   # Correct
   @get("/")
   async def get_items(self): ...
   ```

2. **Incorrect import**
   ```python
   # Make sure to import from the correct module
   from ..cbv import cbv, get
   ```

3. **Router not discovered**
   - Ensure the router variable follows the naming pattern (`*_router`)
   - Check that it's an instance of `BaseRouter`

### Debugging

Enable debug logging to see route registration:
```python
import logging
logging.getLogger("cbv").setLevel(logging.DEBUG)
```

## Examples

### Complete Health Controller

```python
"""Health check routes using Class-Based Views."""

from fastapi import HTTPException

from ...models.health import HealthResponse
from ...services.health import HealthServiceDep
from ..base_router import BaseRouter
from ..cbv import cbv, get

health_router = BaseRouter(prefix="/v1/health", tags=["health"])

@cbv(health_router)
class HealthController:
    """Health check controller with class-based views."""

    @get("/", response_model=HealthResponse, operation_id="get_health_status")
    async def health_check(
        self,
        health_service: HealthServiceDep,
    ) -> HealthResponse:
        """Get application health status."""
        try:
            return await health_service.get_health_status()
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Health check failed: {str(e)}",
            ) from e

    @get("/ready", response_model=HealthResponse)
    async def readiness_check(
        self,
        health_service: HealthServiceDep,
    ) -> HealthResponse:
        """Get application readiness status."""
        try:
            return await health_service.get_readiness_status()
        except Exception as e:
            raise HTTPException(
                status_code=503,
                detail=f"Readiness check failed: {str(e)}",
            ) from e
```

## Conclusion

This CBV implementation provides a clean, maintainable way to organize FastAPI routes while maintaining full compatibility with FastAPI's features including:

- Automatic OpenAPI documentation
- Dependency injection
- Request/response validation
- Error handling
- Middleware support

The implementation is lightweight, type-safe, and integrates seamlessly with the existing codebase structure.

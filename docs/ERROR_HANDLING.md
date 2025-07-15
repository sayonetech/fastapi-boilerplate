# Enhanced Error Handling & Validation

This document describes the enhanced error handling and validation system implemented in the Madcrow FastAPI application.

## Overview

The enhanced error handling system provides:

- **Standardized Error Responses**: Consistent JSON error responses across all endpoints
- **Custom Exception Classes**: Domain-specific exceptions with proper error codes
- **Error Factories**: Utility functions for creating consistent errors
- **Enhanced Validation**: Custom validators with detailed error messages
- **Comprehensive Logging**: Structured error logging with context
- **Development vs Production**: Different error detail levels based on environment

## Architecture

### Exception Hierarchy

```
Exception
├── MadcrowError (Base application exception)
│   ├── MadcrowHTTPError (HTTP-specific exceptions)
│   │   ├── ValidationError
│   │   │   ├── InvalidInputError
│   │   │   ├── MissingFieldError
│   │   │   ├── InvalidFieldValueError
│   │   │   └── SchemaValidationError
│   │   ├── BusinessError
│   │   │   ├── AccountError
│   │   │   │   ├── AccountNotFoundError
│   │   │   │   ├── AccountAlreadyExistsError
│   │   │   │   └── InvalidAccountStatusError
│   │   │   ├── AuthenticationError
│   │   │   └── AuthorizationError
│   │   └── DatabaseError (HTTP-mapped)
│   │       ├── RecordNotFoundError
│   │       └── DuplicateRecordError
│   └── DatabaseError (Non-HTTP)
│       ├── DatabaseConnectionError
│       ├── DatabaseTransactionError
│       └── DatabaseTimeoutError
```

### Components

1. **Exception Classes** (`src/exceptions/`)
   - Base exception classes with error codes and context
   - Domain-specific exceptions for business logic
   - HTTP-specific exceptions that map to status codes

2. **Error Response Models** (`src/models/errors.py`)
   - Pydantic models for standardized error responses
   - Different response types for different error categories

3. **Error Factories** (`src/utils/error_factory.py`)
   - Factory functions for creating consistent errors
   - Response factory for converting exceptions to HTTP responses

4. **Validation Utilities** (`src/utils/validation.py`)
   - Custom validation functions with detailed error messages
   - Pydantic validator creators for common validation patterns

5. **Error Middleware** (`src/middleware/error_middleware.py`)
   - Global exception handling middleware
   - Consistent error response formatting
   - Structured error logging

## Usage Examples

### Creating Custom Exceptions

```python
from src.exceptions import AccountNotFoundError, ValidationError
from src.utils.error_factory import ErrorFactory

# Using specific exception classes
raise AccountNotFoundError(account_id=user_id)

# Using error factory
raise ErrorFactory.create_validation_error(
    field="email",
    message="Invalid email format",
    value="invalid-email"
)
```

### Controller Error Handling Pattern

```python
@cbv(router)
class AccountController:
    @get("/{account_id}")
    async def get_account(self, account_id: UUID) -> AccountResponse:
        # Early validation
        if not account_id:
            raise ErrorFactory.create_validation_error(
                field="account_id",
                message="Account ID is required"
            )

        try:
            account = await account_service.get_by_id(account_id)

            # Guard clause for not found
            if not account:
                raise AccountNotFoundError(account_id=account_id)

            # Happy path
            return AccountResponse.from_orm(account)

        except AccountNotFoundError:
            # Re-raise business logic errors
            raise
        except Exception as e:
            # Convert unexpected errors
            raise ErrorFactory.create_database_error(
                message="Failed to retrieve account",
                operation="select",
                table="accounts",
                cause=e
            )
```

### Validation with Custom Validators

```python
from src.utils.validation import ValidationUtils

class CreateAccountRequest(BaseModel):
    name: str
    email: str
    password: str

    @validator('email', pre=True)
    def validate_email(cls, v):
        return ValidationUtils.validate_email(v)

    @validator('password', pre=True)
    def validate_password(cls, v):
        return ValidationUtils.validate_password(v)
```

## Error Response Format

### Standard Error Response

```json
{
  "error": {
    "code": "ACCOUNT_NOT_FOUND",
    "message": "Account with ID 123e4567-e89b-12d3-a456-426614174000 not found",
    "error_id": "550e8400-e29b-41d4-a716-446655440000"
  }
}
```

### Validation Error Response

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Validation failed for 2 fields",
    "error_id": "550e8400-e29b-41d4-a716-446655440000"
  },
  "details": [
    {
      "field": "email",
      "message": "Invalid email format",
      "code": "INVALID_EMAIL",
      "value": "invalid-email"
    },
    {
      "field": "password",
      "message": "Password must be at least 8 characters",
      "code": "PASSWORD_TOO_SHORT"
    }
  ]
}
```

### Error Response with Context (Debug Mode)

```json
{
  "error": {
    "code": "DATABASE_CONNECTION_FAILED",
    "message": "Unable to connect to database",
    "error_id": "550e8400-e29b-41d4-a716-446655440000",
    "details": {
      "operation": "SELECT",
      "table": "accounts",
      "timeout_seconds": 30
    }
  },
  "path": "/v1/accounts/123",
  "method": "GET",
  "debug": {
    "cause": "Connection timeout",
    "cause_type": "TimeoutError"
  }
}
```

## Best Practices

### 1. Error Handling in Controllers

- **Handle errors early**: Use guard clauses and early returns
- **Validate input first**: Check all input parameters before processing
- **Use specific exceptions**: Prefer domain-specific exceptions over generic ones
- **Re-raise business errors**: Don't catch and convert business logic errors
- **Convert unexpected errors**: Wrap unexpected exceptions in appropriate error types

### 2. Exception Usage

- **Use appropriate exception types**: Choose the most specific exception class
- **Provide context**: Include relevant information in error context
- **Chain exceptions**: Use the `cause` parameter to preserve original exceptions
- **Use error factories**: Prefer factory methods for consistency

### 3. Validation

- **Validate early**: Perform validation as early as possible in the request flow
- **Use custom validators**: Create reusable validation functions
- **Provide clear messages**: Write user-friendly error messages
- **Include expected values**: Show what values are allowed when validation fails

### 4. Logging

- **Log at appropriate levels**: Use different log levels for different error types
- **Include context**: Add request context to error logs
- **Use structured logging**: Include structured data for better analysis
- **Don't log sensitive data**: Avoid logging passwords or tokens

## Configuration

The error handling system respects the following configuration options:

- `DEBUG`: Controls whether debug information is included in error responses
- `DEPLOY_ENV`: Affects error detail levels (more details in development)
- `LOG_LEVEL`: Controls logging verbosity

## Integration

To enable the enhanced error handling system:

1. **Add the extension** to your application initialization:

```python
from src.extensions.ext_error_handling import init_app

def create_app():
    app = FastAPI()
    init_app(app)  # Initialize error handling
    return app
```

2. **Use the error handling patterns** in your controllers as shown in the examples above.

3. **Import and use** the exception classes and utilities in your services and controllers.

## Testing Error Handling

Example test cases for error handling:

```python
def test_account_not_found_error():
    response = client.get("/v1/accounts/nonexistent-id")
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "ACCOUNT_NOT_FOUND"

def test_validation_error():
    response = client.post("/v1/accounts", json={"email": "invalid"})
    assert response.status_code == 422
    assert "details" in response.json()
```

This enhanced error handling system provides a robust foundation for handling errors consistently across the entire application while maintaining good user experience and developer productivity.

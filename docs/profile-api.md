# Profile API Documentation

The Profile API provides endpoints for managing user profile information, including retrieving profile data, updating profile settings, changing passwords, and viewing profile statistics.

## Base URL

All profile endpoints are prefixed with `/api/v1/profile`

## Authentication

All profile endpoints require authentication via JWT token in the `Authorization` header:

```
Authorization: Bearer <jwt_token>
```

## Endpoints

### 1. Get Current User Profile

**Endpoint**: `GET /api/v1/profile/me`

**Description**: Retrieve the complete profile information for the currently authenticated user.

**Request Headers**:

```
Authorization: Bearer <jwt_token>
Content-Type: application/json
```

**Response** (200 OK):

```json
{
  "id": "123e4567-e89b-12d3-a456-426614174000",
  "name": "John Doe",
  "email": "john.doe@example.com",
  "status": "ACTIVE",
  "timezone": "UTC",
  "avatar": "https://example.com/avatar.jpg",
  "is_admin": false,
  "last_login_at": "2024-01-15T10:30:00Z",
  "initialized_at": "2024-01-01T00:00:00Z",
  "created_at": "2024-01-01T00:00:00Z"
}
```

### 2. Update Profile Information

**Endpoint**: `PATCH /api/v1/profile/update`

**Description**: Update user profile information such as name, timezone, and avatar.

**Request Headers**:

```
Authorization: Bearer <jwt_token>
Content-Type: application/json
```

**Request Body**:

```json
{
  "name": "John Doe Updated",
  "timezone": "America/New_York",
  "avatar": "https://example.com/new-avatar.jpg"
}
```

**Response** (200 OK):

```json
{
  "success": true,
  "message": "Profile updated successfully. Updated fields: name, timezone, avatar",
  "user": {
    "id": "123e4567-e89b-12d3-a456-426614174000",
    "name": "John Doe Updated",
    "email": "john.doe@example.com",
    "status": "ACTIVE",
    "timezone": "America/New_York",
    "avatar": "https://example.com/new-avatar.jpg",
    "is_admin": false,
    "last_login_at": "2024-01-15T10:30:00Z",
    "initialized_at": "2024-01-01T00:00:00Z",
    "created_at": "2024-01-01T00:00:00Z"
  },
  "updated_at": "2024-01-15T14:30:00Z"
}
```

### 3. Change Password

**Endpoint**: `POST /api/v1/profile/change-password`

**Description**: Change user password by providing current password and new password.

**Request Headers**:

```
Authorization: Bearer <jwt_token>
Content-Type: application/json
```

**Request Body**:

```json
{
  "current_password": "oldpassword123", // pragma: allowlist secret
  "new_password": "newstrongpassword456" // pragma: allowlist secret
}
```

**Response** (200 OK):

```json
{
  "success": true,
  "message": "Password changed successfully",
  "changed_at": "2024-01-15T12:00:00Z"
}
```

### 4. Get Profile Statistics

**Endpoint**: `GET /api/v1/profile/stats`

**Description**: Get user profile statistics including account age, activity status, and profile completion.

**Request Headers**:

```
Authorization: Bearer <jwt_token>
Content-Type: application/json
```

**Response** (200 OK):

```json
{
  "user_id": "123e4567-e89b-12d3-a456-426614174000",
  "account_age_days": 45,
  "last_login_days_ago": 2,
  "is_recently_active": true,
  "profile_completion": 0.8,
  "missing_fields": ["avatar", "timezone"]
}
```

### 5. Alternative Profile Endpoint (Decorator Demo)

**Endpoint**: `GET /api/v1/profile/me-alt`

**Description**: Alternative profile endpoint demonstrating the `@login_required` decorator usage.

**Request Headers**:

```
Authorization: Bearer <jwt_token>
Content-Type: application/json
```

**Response** (200 OK):

```json
{
  "message": "Profile retrieved using @login_required decorator",
  "user": {
    "id": "123e4567-e89b-12d3-a456-426614174000",
    "name": "John Doe",
    "email": "john.doe@example.com",
    "is_admin": false,
    "status": "ACTIVE",
    "timezone": "UTC",
    "avatar": "https://example.com/avatar.jpg",
    "last_login_at": "2024-01-15T10:30:00Z",
    "created_at": "2024-01-01T00:00:00Z"
  },
  "decorator_used": "login_required",
  "note": "This demonstrates an alternative to CurrentUser dependency injection"
}
```

## Error Responses

### 401 Unauthorized

```json
{
  "detail": "Authentication required"
}
```

### 400 Bad Request (Password Change)

```json
{
  "detail": "Current password is incorrect"
}
```

### 422 Validation Error

```json
{
  "detail": [
    {
      "loc": ["body", "name"],
      "msg": "ensure this value has at least 1 characters",
      "type": "value_error.any_str.min_length"
    }
  ]
}
```

### 500 Internal Server Error

```json
{
  "detail": "Profile update failed due to system error"
}
```

## Migration from Auth Endpoints

The following endpoint has been moved from `/api/v1/auth` to `/api/v1/profile`:

- `GET /api/v1/auth/me` → `GET /api/v1/profile/me`

The old endpoint has been removed. Please update your client applications to use the new profile endpoints.

## Field Validation

### Profile Update Fields

- **name**: 1-255 characters, optional
- **timezone**: Valid timezone string (e.g., "UTC", "America/New_York"), optional
- **avatar**: Valid URL up to 500 characters, optional

### Password Change Fields

- **current_password**: Required, minimum 1 character
- **new_password**: Required, minimum 8 characters, must meet password strength requirements

## Profile Completion Calculation

The profile completion percentage is calculated based on the following fields:

- Name (always present)
- Email (always present)
- Timezone (optional)
- Avatar (optional)
- Status (always present)
- Admin flag (always present)

Total: 6 fields, completion = (completed_fields / 6) \* 100%

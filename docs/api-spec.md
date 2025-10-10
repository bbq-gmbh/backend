# API Specification

Complete REST API reference for fs-backend.

**Base URL (Development)**: `http://127.0.0.1:3001`

## Authentication

All protected endpoints require a JWT access token in the `Authorization` header:
```
Authorization: Bearer <access_token>
```

## Endpoints

### Authentication Endpoints

#### POST /auth/register
Register a new user and receive authentication tokens.

**Authentication**: None required

**Request Body**:
```json
{
  "username": "string",
  "password": "string"
}
```

**Validation Rules**:
- `username`: ≥4 characters, no whitespace
- `password`: ≥8 characters

**Success Response** (200):
```json
{
  "access_token": "eyJhbGc...",
  "refresh_token": "eyJhbGc...",
  "token_type": "bearer"
}
```

**Error Responses**:
- `409 Conflict`: Username already exists
- `422 Unprocessable Entity`: Validation failed

**Example**:
```bash
curl -X POST http://127.0.0.1:3001/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username": "johndoe", "password": "securepass123"}'
```

---

#### POST /auth/login
Authenticate with username and password.

**Authentication**: None required

**Request Body**:
```json
{
  "username": "string",
  "password": "string"
}
```

**Success Response** (200):
```json
{
  "access_token": "eyJhbGc...",
  "refresh_token": "eyJhbGc...",
  "token_type": "bearer"
}
```

**Error Responses**:
- `401 Unauthorized`: Invalid credentials
- `422 Unprocessable Entity`: Validation failed

**Example**:
```bash
curl -X POST http://127.0.0.1:3001/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "johndoe", "password": "securepass123"}'
```

---

#### POST /auth/refresh
Obtain a new access token using a refresh token.

**Authentication**: None required (refresh token in body)

**Request Body**:
```json
{
  "refresh_token": "string"
}
```

**Success Response** (200):
```json
{
  "access_token": "eyJhbGc...",
  "token_type": "bearer"
}
```

**Error Responses**:
- `401 Unauthorized`: Invalid or expired refresh token
- `422 Unprocessable Entity`: Missing refresh token

**Example**:
```bash
curl -X POST http://127.0.0.1:3001/auth/refresh \
  -H "Content-Type: application/json" \
  -d '{"refresh_token": "eyJhbGc..."}'
```

---

#### POST /auth/logout-all
Invalidate all tokens for the current user across all devices.

**Authentication**: Required (access token)

**Request Body**: None

**Success Response** (204):
No content

**Error Responses**:
- `401 Unauthorized`: Invalid or missing token

**Example**:
```bash
curl -X POST http://127.0.0.1:3001/auth/logout-all \
  -H "Authorization: Bearer eyJhbGc..."
```

**Note**: This rotates the user's `token_version`, invalidating all existing tokens.

---

#### POST /auth/change-password
Change the current user's password.

**Authentication**: Required (access token)

**Request Body**:
```json
{
  "current_password": "string",
  "new_password": "string"
}
```

**Validation Rules**:
- `new_password`: ≥8 characters

**Success Response** (204):
No content

**Error Responses**:
- `401 Unauthorized`: Invalid current password or missing token
- `422 Unprocessable Entity`: Validation failed

**Example**:
```bash
curl -X POST http://127.0.0.1:3001/auth/change-password \
  -H "Authorization: Bearer eyJhbGc..." \
  -H "Content-Type: application/json" \
  -d '{"current_password": "oldpass123", "new_password": "newpass456"}'
```

**Note**: This also rotates the user's `token_version`, requiring re-authentication on all devices.

---

### User Management Endpoints

#### POST /users
Create a new user (admin function).

**Authentication**: Required (access token)

**Request Body**:
```json
{
  "username": "string",
  "password": "string"
}
```

**Validation Rules**:
- `username`: ≥4 characters, no whitespace
- `password`: ≥8 characters

**Success Response** (201):
```json
{
  "id": "uuid",
  "username": "string",
  "created_at": "2025-10-10T12:00:00",
  "updated_at": "2025-10-10T12:00:00"
}
```

**Error Responses**:
- `401 Unauthorized`: Missing or invalid token
- `409 Conflict`: Username already exists
- `422 Unprocessable Entity`: Validation failed

**Example**:
```bash
curl -X POST http://127.0.0.1:3001/users \
  -H "Authorization: Bearer eyJhbGc..." \
  -H "Content-Type: application/json" \
  -d '{"username": "newuser", "password": "password123"}'
```

---

#### GET /users
Retrieve a list of all users.

**Authentication**: Required (access token)

**Query Parameters**: None (pagination to be added)

**Success Response** (200):
```json
[
  {
    "id": "uuid",
    "username": "string",
    "created_at": "2025-10-10T12:00:00",
    "updated_at": "2025-10-10T12:00:00"
  },
  {
    "id": "uuid",
    "username": "string",
    "created_at": "2025-10-10T12:00:00",
    "updated_at": "2025-10-10T12:00:00"
  }
]
```

**Error Responses**:
- `401 Unauthorized`: Missing or invalid token

**Example**:
```bash
curl -X GET http://127.0.0.1:3001/users \
  -H "Authorization: Bearer eyJhbGc..."
```

---

### Root Endpoint

#### GET /
Health check and welcome message.

**Authentication**: None required

**Success Response** (200):
```json
{
  "message": "Welcome to the User API"
}
```

---

## Common Response Formats

### Success Responses
All successful responses follow standard HTTP status codes:
- `200 OK`: Successful request with response body
- `201 Created`: Resource successfully created
- `204 No Content`: Successful request with no response body

### Error Responses
All errors return a JSON object with a `detail` field:

```json
{
  "detail": "Error message describing what went wrong"
}
```

#### HTTP Status Codes

| Status | Meaning | When Used |
|--------|---------|-----------|
| `400` | Bad Request | General domain error |
| `401` | Unauthorized | Invalid credentials, expired/invalid token, token version mismatch |
| `404` | Not Found | User not found |
| `409` | Conflict | Username already exists |
| `422` | Unprocessable Entity | Validation error (username/password rules) |
| `500` | Internal Server Error | Unexpected server error |

### Example Error Responses

**401 Unauthorized**:
```json
{
  "detail": "Invalid authentication credentials"
}
```

**409 Conflict**:
```json
{
  "detail": "Username already exists"
}
```

**422 Validation Error**:
```json
{
  "detail": "Username must be at least 4 characters"
}
```

---

## Data Models

### TokenPair
```typescript
{
  access_token: string;   // JWT, expires in 15 minutes
  refresh_token: string;  // JWT, expires in 7 days
  token_type: string;     // Always "bearer"
}
```

### AccessToken
```typescript
{
  access_token: string;   // JWT, expires in 15 minutes
  token_type: string;     // Always "bearer"
}
```

### UserRead
```typescript
{
  id: string;             // UUID
  username: string;
  created_at: string;     // ISO 8601 datetime
  updated_at: string;     // ISO 8601 datetime
}
```

### UserCreate
```typescript
{
  username: string;       // ≥4 chars, no whitespace
  password: string;       // ≥8 chars
}
```

---

## JWT Token Structure

### Access Token Claims
```json
{
  "sub": "user-id-uuid",
  "token_version": "uuid",
  "token_kind": "access",
  "iat": 1728518400,
  "exp": 1728522000
}
```

### Refresh Token Claims
```json
{
  "sub": "user-id-uuid",
  "token_version": "uuid",
  "token_kind": "refresh",
  "iat": 1728518400,
  "exp": 1729123200
}
```

**Token Lifetimes**:
- Access Token: 15 minutes (900 seconds)
- Refresh Token: 7 days (604,800 seconds)

---

## Rate Limiting

⚠️ **Not Yet Implemented**: Rate limiting is planned for production but not currently enforced.

**Planned Limits**:
- Login attempts: 5 per minute per IP
- General API calls: 100 per minute per user

---

## Interactive Documentation

When the server is running, you can access:
- **Swagger UI**: http://127.0.0.1:3001/docs
- **ReDoc**: http://127.0.0.1:3001/redoc

These provide interactive API exploration and testing capabilities.

---

## Testing Examples

### Complete User Flow

```bash
# 1. Register a new user
RESPONSE=$(curl -s -X POST http://127.0.0.1:3001/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username": "testuser", "password": "testpass123"}')

ACCESS_TOKEN=$(echo $RESPONSE | jq -r '.access_token')
REFRESH_TOKEN=$(echo $RESPONSE | jq -r '.refresh_token')

# 2. Access protected endpoint
curl -X GET http://127.0.0.1:3001/users \
  -H "Authorization: Bearer $ACCESS_TOKEN"

# 3. Refresh the access token
NEW_RESPONSE=$(curl -s -X POST http://127.0.0.1:3001/auth/refresh \
  -H "Content-Type: application/json" \
  -d "{\"refresh_token\": \"$REFRESH_TOKEN\"}")

NEW_ACCESS_TOKEN=$(echo $NEW_RESPONSE | jq -r '.access_token')

# 4. Change password
curl -X POST http://127.0.0.1:3001/auth/change-password \
  -H "Authorization: Bearer $NEW_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"current_password": "testpass123", "new_password": "newpass456"}'

# 5. Old tokens are now invalid, must login again
curl -X POST http://127.0.0.1:3001/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "testuser", "password": "newpass456"}'
```

---

## References
- [Authentication Flow Details](authentication.md)
- [Error Handling Guide](errors.md)
- [Architecture Overview](architecture.md)

---
*Last Updated: October 10, 2025*

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

# API Specification

Complete REST API reference for fs-backend.

**Base URL (Development)**: `http://127.0.0.1:3001`  
**Base URL (Production)**: `https://api.example.com` _(configure as needed)_

---

## Authentication

All protected endpoints require a JWT access token in the `Authorization` header:
```
Authorization: Bearer <access_token>
```

Token format: JWT (JSON Web Token) with 15-minute expiry.

Get tokens via:
- `/auth/register` - Register new user
- `/auth/login` - Login with credentials
- `/auth/refresh` - Refresh expired access token

---

## Overview: Endpoint Categories

| Category | Endpoints | Protected |
|----------|-----------|-----------|
| **Auth** | Register, Login, Logout, Refresh, Password | Mostly No |
| **Me** | Current user profile | Yes |
| **Users** | CRUD, Search | Yes |
| **Employees** | Profile, Hierarchy | Yes |
| **Time Entries** | Create, Query, Delete | Yes |
| **Absence Entries** | Create, Query, Delete | Yes |

---

## Authentication Endpoints

### POST /auth/register
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
- `username`: Minimum 4 characters, no whitespace, must be unique
- `password`: Minimum 8 characters

**Success Response** (200):
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

**Error Responses**:
- `409 Conflict`: Username already exists
- `422 Unprocessable Entity`: Validation failed (username/password rules)

**Example**:
```bash
curl -X POST http://127.0.0.1:3001/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "john.doe",
    "password": "SecurePass123!"
  }'
```

---

### POST /auth/login
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
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

**Error Responses**:
- `401 Unauthorized`: Invalid username or password
- `422 Unprocessable Entity`: Missing fields

**Example**:
```bash
curl -X POST http://127.0.0.1:3001/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "john.doe",
    "password": "SecurePass123!"
  }'
```

---

### POST /auth/refresh
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
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
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

**Note**: Returns new access AND refresh tokens. Old tokens become invalid.

---

### POST /auth/logout-all
Invalidate all tokens for the current user across all devices.

**Authentication**: Required (access token)

**Request Body**: None

**Success Response** (204): No content

**Error Responses**:
- `401 Unauthorized`: Invalid or missing token

**Example**:
```bash
curl -X POST http://127.0.0.1:3001/auth/logout-all \
  -H "Authorization: Bearer eyJhbGc..."
```

**Note**: Rotates user's token_key, invalidating all previously issued tokens. User must re-login on all devices.

---

### POST /auth/change-password
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
- `current_password`: Must match current password
- `new_password`: Minimum 8 characters, must differ from current password

**Success Response** (204): No content

**Error Responses**:
- `401 Unauthorized`: Invalid current password or missing token
- `422 Unprocessable Entity`: Validation failed

**Example**:
```bash
curl -X POST http://127.0.0.1:3001/auth/change-password \
  -H "Authorization: Bearer eyJhbGc..." \
  -H "Content-Type: application/json" \
  -d '{
    "current_password": "OldPass123!",
    "new_password": "NewPass456!"
  }'
```

**Note**: Rotates token_key; all tokens become invalid. User must re-login.

---

### POST /auth/remote-logout-all
**(Superuser Only)** Invalidate all sessions for a user.

**Authentication**: Required (superuser access token)

**Request Body**:
```json
{
  "user_id": "uuid"
}
```

**Success Response** (204): No content

**Error Responses**:
- `401 Unauthorized`: Not superuser
- `404 Not Found`: User not found

**Example**:
```bash
curl -X POST http://127.0.0.1:3001/auth/remote-logout-all \
  -H "Authorization: Bearer <admin_token>" \
  -H "Content-Type: application/json" \
  -d '{"user_id": "550e8400-e29b-41d4-a716-446655440000"}'
```

---

### POST /auth/remote-reset-password
**(Superuser Only)** Reset password for a user and return temporary password.

**Authentication**: Required (superuser access token)

**Request Body**:
```json
{
  "user_id": "uuid"
}
```

**Success Response** (200):
```json
{
  "temporary_password": "Tr0pic@lWxY9#Kp2"
}
```

**Error Responses**:
- `401 Unauthorized`: Not superuser
- `404 Not Found`: User not found

**Example**:
```bash
curl -X POST http://127.0.0.1:3001/auth/remote-reset-password \
  -H "Authorization: Bearer <admin_token>" \
  -H "Content-Type: application/json" \
  -d '{"user_id": "550e8400-e29b-41d4-a716-446655440000"}'
```

---

## Me Endpoint

### GET /me
Get current authenticated user information.

**Authentication**: Required (access token)

**Success Response** (200):
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "username": "john.doe",
  "is_superuser": false,
  "created_at": "2025-11-07T10:30:00Z",
  "employee": {
    "first_name": "John",
    "last_name": "Doe",
    "birthday": "1990-05-15"
  }
}
```

If user has no employee profile, `employee` field is `null`.

**Error Responses**:
- `401 Unauthorized`: Invalid or missing token

**Example**:
```bash
curl http://127.0.0.1:3001/me \
  -H "Authorization: Bearer <token>"
```

---

## User Management Endpoints

### POST /users
**(Protected)** Create a new user.

**Authentication**: Required (access token)

**Request Body**:
```json
{
  "username": "string",
  "password": "string"
}
```

**Success Response** (201):
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "username": "jane.smith",
  "is_superuser": false,
  "created_at": "2025-11-07T10:35:00Z",
  "employee": null
}
```

**Error Responses**:
- `401 Unauthorized`: Missing token
- `409 Conflict`: Username already exists
- `422 Unprocessable Entity`: Validation failed

**Example**:
```bash
curl -X POST http://127.0.0.1:3001/users \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"username": "jane.smith", "password": "password123"}'
```

---

### GET /users
**(Protected)** List users with pagination and filtering.

**Authentication**: Required (access token)

**Query Parameters**:
- `page` (integer, required): Page number (0-indexed)
- `page_size` (integer, required): Items per page (1-200)
- `is_employee` (boolean, optional): Filter by employee status
- `superuser` (boolean, optional): Filter by superuser status

**Success Response** (200):
```json
{
  "page": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "username": "john.doe",
      "is_superuser": false,
      "created_at": "2025-11-07T10:30:00Z",
      "employee": {
        "first_name": "John",
        "last_name": "Doe",
        "birthday": "1990-05-15"
      }
    }
  ],
  "total": 42
}
```

**Error Responses**:
- `401 Unauthorized`: Missing token

**Example**:
```bash
curl 'http://127.0.0.1:3001/users?page=0&page_size=10' \
  -H "Authorization: Bearer <token>"

curl 'http://127.0.0.1:3001/users?page=0&page_size=10&is_employee=true' \
  -H "Authorization: Bearer <token>"
```

**Authorization**: 
- Superusers see all users
- Regular users see only employees in their hierarchy

---

### GET /users/search
**(Protected)** Search users by username.

**Authentication**: Required (access token)

**Query Parameters**:
- `query` (string, required): Search term (minimum 1 character)
- `page` (integer, required): Page number
- `page_size` (integer, required): Items per page (1-200)
- `is_employee` (boolean, optional): Filter by employee status

**Success Response** (200):
```json
{
  "page": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "username": "john.doe",
      "is_superuser": false,
      "created_at": "2025-11-07T10:30:00Z",
      "employee": {
        "first_name": "John",
        "last_name": "Doe",
        "birthday": "1990-05-15"
      }
    }
  ],
  "total": 5
}
```

**Error Responses**:
- `401 Unauthorized`: Missing token
- `422 Unprocessable Entity`: Query too short

**Example**:
```bash
curl 'http://127.0.0.1:3001/users/search?query=john&page=0&page_size=10' \
  -H "Authorization: Bearer <token>"
```

---

### GET /users/{id}
**(Protected)** Get user by ID.

**Authentication**: Required (access token)

**Path Parameters**:
- `id` (UUID): User ID

**Success Response** (200):
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "username": "john.doe",
  "is_superuser": false,
  "created_at": "2025-11-07T10:30:00Z",
  "employee": {
    "first_name": "John",
    "last_name": "Doe",
    "birthday": "1990-05-15"
  }
}
```

**Error Responses**:
- `401 Unauthorized`: Missing token
- `403 Forbidden`: Not authorized to view this user
- `404 Not Found`: User not found

**Example**:
```bash
curl http://127.0.0.1:3001/users/550e8400-e29b-41d4-a716-446655440000 \
  -H "Authorization: Bearer <token>"
```

**Authorization**:
- Superusers can view any user
- Regular users can only view employees in their hierarchy

---

### DELETE /users/{id}
**(Superuser Only)** Delete a user.

**Authentication**: Required (superuser access token)

**Path Parameters**:
- `id` (UUID): User ID to delete

**Success Response** (204): No content

**Error Responses**:
- `401 Unauthorized`: Not superuser
- `404 Not Found`: User not found

**Example**:
```bash
curl -X DELETE http://127.0.0.1:3001/users/550e8400-e29b-41d4-a716-446655440000 \
  -H "Authorization: Bearer <admin_token>"
```

---

### GET /users/exists/{id}
**(Superuser Only)** Check if user ID exists.

**Authentication**: Required (superuser access token)

**Path Parameters**:
- `id` (UUID): User ID to check

**Success Response** (204): No content (user exists)

**Error Responses**:
- `401 Unauthorized`: Not superuser
- `404 Not Found`: User does not exist

**Example**:
```bash
curl -I http://127.0.0.1:3001/users/exists/550e8400-e29b-41d4-a716-446655440000 \
  -H "Authorization: Bearer <admin_token>"
```

---

### GET /users/exists/username/{name}
**(Superuser Only)** Check if username exists.

**Authentication**: Required (superuser access token)

**Path Parameters**:
- `name` (string): Username to check

**Success Response** (204): No content (username exists)

**Error Responses**:
- `401 Unauthorized`: Not superuser
- `404 Not Found`: Username does not exist

**Example**:
```bash
curl -I http://127.0.0.1:3001/users/exists/username/john.doe \
  -H "Authorization: Bearer <admin_token>"
```

---

## Employee Management Endpoints

### GET /employees/me
**(Protected)** Get current user's employee profile.

**Authentication**: Required (access token)

**Success Response** (200):
```json
{
  "user_id": "550e8400-e29b-41d4-a716-446655440000",
  "first_name": "John",
  "last_name": "Doe",
  "birthday": "1990-05-15",
  "hour_model": "e40",
  "pause_time_minutes": 30,
  "start_from": "2024-01-15",
  "supervisor_id": "550e8400-e29b-41d4-a716-446655440001"
}
```

Returns `null` if user has no employee profile.

**Error Responses**:
- `401 Unauthorized`: Missing token

**Example**:
```bash
curl http://127.0.0.1:3001/employees/me \
  -H "Authorization: Bearer <token>"
```

---

### POST /employees
**(Superuser Only)** Create employee profile.

**Authentication**: Required (superuser access token)

**Request Body**:
```json
{
  "user_id": "550e8400-e29b-41d4-a716-446655440000",
  "first_name": "John",
  "last_name": "Doe",
  "birthday": "1990-05-15",
  "hour_model": "e40",
  "pause_time_minutes": 30,
  "start_from": "2024-01-15",
  "supervisor_id": "550e8400-e29b-41d4-a716-446655440001"
}
```

**Success Response** (201):
```json
{
  "user_id": "550e8400-e29b-41d4-a716-446655440000",
  "first_name": "John",
  "last_name": "Doe",
  "birthday": "1990-05-15",
  "hour_model": "e40",
  "pause_time_minutes": 30,
  "start_from": "2024-01-15",
  "supervisor_id": "550e8400-e29b-41d4-a716-446655440001"
}
```

**Error Responses**:
- `401 Unauthorized`: Not superuser
- `409 Conflict`: Employee already exists for user
- `422 Unprocessable Entity`: Validation failed

**Example**:
```bash
curl -X POST http://127.0.0.1:3001/employees \
  -H "Authorization: Bearer <admin_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "550e8400-e29b-41d4-a716-446655440000",
    "first_name": "John",
    "last_name": "Doe",
    "birthday": "1990-05-15",
    "hour_model": "e40",
    "pause_time_minutes": 30,
    "start_from": "2024-01-15"
  }'
```

---

### GET /employees/{user_id}
**(Protected)** Get employee profile by user ID.

**Authentication**: Required (access token)

**Path Parameters**:
- `user_id` (UUID): User ID

**Success Response** (200):
```json
{
  "user_id": "550e8400-e29b-41d4-a716-446655440000",
  "first_name": "John",
  "last_name": "Doe",
  "birthday": "1990-05-15",
  "hour_model": "e40",
  "pause_time_minutes": 30,
  "start_from": "2024-01-15",
  "supervisor_id": "550e8400-e29b-41d4-a716-446655440001"
}
```

**Error Responses**:
- `401 Unauthorized`: Missing token
- `403 Forbidden`: Not authorized to view
- `404 Not Found`: Employee not found

**Example**:
```bash
curl http://127.0.0.1:3001/employees/550e8400-e29b-41d4-a716-446655440000 \
  -H "Authorization: Bearer <token>"
```

---

### GET /employees/{user_id}/hierarchy
**(Protected)** Get employee hierarchy (supervisors and subordinates).

**Authentication**: Required (access token)

**Path Parameters**:
- `user_id` (UUID): User ID

**Success Response** (200):
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "first_name": "John",
  "last_name": "Doe",
  "supervisors": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440001",
      "first_name": "Jane",
      "last_name": "Manager"
    }
  ],
  "subordinates": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440002",
      "first_name": "Bob",
      "last_name": "Developer"
    }
  ]
}
```

**Error Responses**:
- `401 Unauthorized`: Missing token
- `403 Forbidden`: Not authorized to view hierarchy
- `404 Not Found`: Employee not found

**Example**:
```bash
curl http://127.0.0.1:3001/employees/550e8400-e29b-41d4-a716-446655440000/hierarchy \
  -H "Authorization: Bearer <token>"
```

**Authorization**:
- Superusers can view any hierarchy
- Employees can only view their own hierarchy and subordinates

---

## Time Entry Endpoints

### POST /time_entries
**(Protected)** Create time entry (arrival/departure).

**Authentication**: Required (access token)

**Request Body**:
```json
{
  "user_id": "550e8400-e29b-41d4-a716-446655440000",
  "entry_type": "arrival",
  "date_time": "2025-11-07T08:30:00Z"
}
```

**Query Parameters**:
- `force` (boolean, optional): Override validation rules (superuser only)

**Success Response** (201):
```json
{
  "id": 1,
  "user_id": "550e8400-e29b-41d4-a716-446655440000",
  "entry_type": "arrival",
  "date_time": "2025-11-07T08:30:00Z",
  "created_by": "550e8400-e29b-41d4-a716-446655440000",
  "created_at": "2025-11-07T08:31:00Z"
}
```

**Error Responses**:
- `401 Unauthorized`: Missing token
- `403 Forbidden`: Not authorized to create for this user
- `404 Not Found`: Employee not found
- `422 Unprocessable Entity`: Validation failed

**Example**:
```bash
curl -X POST http://127.0.0.1:3001/time_entries \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "550e8400-e29b-41d4-a716-446655440000",
    "entry_type": "arrival",
    "date_time": "2025-11-07T08:30:00Z"
  }'
```

**Authorization**:
- Users can create entries for themselves
- Supervisors can create for subordinates
- Superusers can create for anyone

---

### POST /time_entries/get
**(Protected)** Query time entries by date or range.

**Authentication**: Required (access token)

**Request Body**:
```json
{
  "user_id": "550e8400-e29b-41d4-a716-446655440000",
  "date_from": "2025-11-01",
  "date_to": "2025-11-07"
}
```

Or query single day:
```json
{
  "user_id": "550e8400-e29b-41d4-a716-446655440000",
  "date": "2025-11-07"
}
```

**Success Response** (200):
```json
[
  {
    "id": 1,
    "user_id": "550e8400-e29b-41d4-a716-446655440000",
    "entry_type": "arrival",
    "date_time": "2025-11-07T08:30:00Z",
    "created_by": "550e8400-e29b-41d4-a716-446655440000",
    "created_at": "2025-11-07T08:31:00Z"
  },
  {
    "id": 2,
    "user_id": "550e8400-e29b-41d4-a716-446655440000",
    "entry_type": "departure",
    "date_time": "2025-11-07T17:30:00Z",
    "created_by": "550e8400-e29b-41d4-a716-446655440000",
    "created_at": "2025-11-07T17:31:00Z"
  }
]
```

**Error Responses**:
- `401 Unauthorized`: Missing token
- `403 Forbidden`: Not authorized
- `404 Not Found`: Employee not found

**Example**:
```bash
curl -X POST http://127.0.0.1:3001/time_entries/get \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "550e8400-e29b-41d4-a716-446655440000",
    "date_from": "2025-11-01",
    "date_to": "2025-11-07"
  }'
```

---

### DELETE /time_entries
**(Protected)** Delete a time entry.

**Authentication**: Required (access token)

**Request Body**:
```json
{
  "id": 1
}
```

**Query Parameters**:
- `force` (boolean, optional): Override edit window (superuser only)

**Success Response** (204): No content

**Error Responses**:
- `401 Unauthorized`: Missing token
- `403 Forbidden`: Not authorized to delete
- `404 Not Found`: Entry not found
- `422 Unprocessable Entity`: Entry outside edit window

**Example**:
```bash
curl -X DELETE http://127.0.0.1:3001/time_entries \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"id": 1}'
```

---

## Absence Entry Endpoints

### POST /absence_entries
**(Protected)** Create absence entry (sickness, vacation, etc.).

**Authentication**: Required (access token)

**Request Body**:
```json
{
  "user_id": "550e8400-e29b-41d4-a716-446655440000",
  "entry_type": "vacation",
  "date_begin": "2025-11-10",
  "date_end": "2025-11-14"
}
```

**Query Parameters**:
- `force` (boolean, optional): Override validation (superuser only)
- `dry` (boolean, optional): Dry run without persisting

**Success Response** (201):
```json
{
  "id": 1,
  "user_id": "550e8400-e29b-41d4-a716-446655440000",
  "entry_type": "vacation",
  "date_begin": "2025-11-10",
  "date_end": "2025-11-14",
  "created_by": "550e8400-e29b-41d4-a716-446655440000",
  "created_at": "2025-11-07T10:00:00Z"
}
```

**Error Responses**:
- `401 Unauthorized`: Missing token
- `403 Forbidden`: Not authorized
- `404 Not Found`: Employee not found
- `422 Unprocessable Entity`: Validation failed

**Example**:
```bash
curl -X POST http://127.0.0.1:3001/absence_entries \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "550e8400-e29b-41d4-a716-446655440000",
    "entry_type": "vacation",
    "date_begin": "2025-11-10",
    "date_end": "2025-11-14"
  }'
```

---

### POST /absence_entries/get
**(Protected)** Query absence entries.

**Authentication**: Required (access token)

**Request Body**:
```json
{
  "user_id": "550e8400-e29b-41d4-a716-446655440000",
  "date_from": "2025-11-01",
  "date_to": "2025-11-30"
}
```

**Success Response** (200):
```json
[
  {
    "id": 1,
    "user_id": "550e8400-e29b-41d4-a716-446655440000",
    "entry_type": "vacation",
    "date_begin": "2025-11-10",
    "date_end": "2025-11-14",
    "created_by": "550e8400-e29b-41d4-a716-446655440000",
    "created_at": "2025-11-07T10:00:00Z"
  }
]
```

**Error Responses**:
- `401 Unauthorized`: Missing token
- `403 Forbidden`: Not authorized
- `404 Not Found`: Employee not found

**Example**:
```bash
curl -X POST http://127.0.0.1:3001/absence_entries/get \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "550e8400-e29b-41d4-a716-446655440000",
    "date_from": "2025-11-01",
    "date_to": "2025-11-30"
  }'
```

---

### DELETE /absence_entries
**(Protected)** Delete an absence entry.

**Authentication**: Required (access token)

**Request Body**:
```json
{
  "id": 1
}
```

**Query Parameters**:
- `force` (boolean, optional): Override restrictions (superuser only)

**Success Response** (204): No content

**Error Responses**:
- `401 Unauthorized`: Missing token
- `403 Forbidden`: Not authorized to delete
- `404 Not Found`: Entry not found

**Example**:
```bash
curl -X DELETE http://127.0.0.1:3001/absence_entries \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"id": 1}'
```

---

## Health Check

### GET /
Health check and welcome endpoint.

**Authentication**: None required

**Success Response** (200): Empty response body (200 OK indicates system is healthy)

**Example**:
```bash
curl http://127.0.0.1:3001/
```

---

## Common Response Formats

### Success Responses
All successful responses follow standard HTTP status codes:
- `200 OK`: Request succeeded with response body
- `201 Created`: Resource created successfully
- `204 No Content`: Request succeeded, no response body

### Error Responses
All errors return JSON with `detail` field:

```json
{
  "detail": "Error message describing what went wrong"
}
```

#### HTTP Status Codes

| Status | Meaning | When Used |
|--------|---------|-----------|
| `400` | Bad Request | General validation error |
| `401` | Unauthorized | Invalid/missing token, authentication failed |
| `403` | Forbidden | Insufficient permissions/authorization |
| `404` | Not Found | Resource does not exist |
| `409` | Conflict | Resource already exists (e.g., username) |
| `422` | Unprocessable Entity | Validation error in input |
| `500` | Internal Server Error | Unexpected server error |

### Example Error Responses

**401 Unauthorized** (invalid token):
```json
{
  "detail": "Invalid authentication credentials"
}
```

**403 Forbidden**:
```json
{
  "detail": "Not authorized to perform this action"
}
```

**404 Not Found**:
```json
{
  "detail": "User '550e8400-e29b-41d4-a716-446655440000' not found"
}
```

**409 Conflict**:
```json
{
  "detail": "Username 'john.doe' already exists"
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
```json
{
  "access_token": "string",   // JWT, expires in 15-30 minutes
  "refresh_token": "string",  // JWT, expires in 7 days
  "token_type": "bearer"
}
```

### UserInfo
```json
{
  "id": "uuid",
  "username": "string",
  "is_superuser": boolean,
  "created_at": "ISO-8601 datetime",
  "employee": {
    "first_name": "string",
    "last_name": "string",
    "birthday": "YYYY-MM-DD"
  } | null
}
```

### EmployeeProfile
```json
{
  "user_id": "uuid",
  "first_name": "string",
  "last_name": "string",
  "birthday": "YYYY-MM-DD",
  "hour_model": "e30|e35|e40",
  "pause_time_minutes": integer,
  "start_from": "YYYY-MM-DD",
  "supervisor_id": "uuid|null"
}
```

### TimeEntry
```json
{
  "id": integer,
  "user_id": "uuid",
  "entry_type": "arrival|departure",
  "date_time": "ISO-8601 datetime",
  "created_by": "uuid",
  "created_at": "ISO-8601 datetime"
}
```

### AbsenceEntry
```json
{
  "id": integer,
  "user_id": "uuid",
  "entry_type": "sickness|vacation|other",
  "date_begin": "YYYY-MM-DD",
  "date_end": "YYYY-MM-DD",
  "created_by": "uuid",
  "created_at": "ISO-8601 datetime"
}
```

---

## Interactive Documentation

When the server is running, access these interfaces:
- **Swagger UI**: http://127.0.0.1:3001/docs
  - Try out endpoints interactively
  - See request/response examples
  - View schema definitions

- **ReDoc**: http://127.0.0.1:3001/redoc
  - Read-only documentation
  - Better for reference
  - Print-friendly

---

## Complete Example: User Registration Flow

```bash
#!/bin/bash
BASE_URL="http://127.0.0.1:3001"

# 1. Register new user
echo "1. Registering user..."
REGISTER_RESPONSE=$(curl -s -X POST $BASE_URL/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "john.employee",
    "password": "SecurePass123!"
  }')

ACCESS_TOKEN=$(echo $REGISTER_RESPONSE | jq -r '.access_token')
REFRESH_TOKEN=$(echo $REGISTER_RESPONSE | jq -r '.refresh_token')

echo "Access token: $ACCESS_TOKEN"
echo "Refresh token: $REFRESH_TOKEN"

# 2. Get current user info
echo -e "\n2. Getting current user..."
curl -s $BASE_URL/me \
  -H "Authorization: Bearer $ACCESS_TOKEN" | jq

# 3. Refresh tokens
echo -e "\n3. Refreshing tokens..."
NEW_TOKENS=$(curl -s -X POST $BASE_URL/auth/refresh \
  -H "Content-Type: application/json" \
  -d "{\"refresh_token\": \"$REFRESH_TOKEN\"}")

NEW_ACCESS_TOKEN=$(echo $NEW_TOKENS | jq -r '.access_token')

# 4. Change password
echo -e "\n4. Changing password..."
curl -s -X POST $BASE_URL/auth/change-password \
  -H "Authorization: Bearer $NEW_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "current_password": "SecurePass123!",
    "new_password": "NewPassword456!"
  }'

echo "Success!"
```

---

## References
- [Authentication Flow](authentication.md)
- [Authorization & RBAC](authentication.md#authorization-role-based-access-control)
- [Error Handling](errors.md)
- [Architecture Overview](architecture.md)
- [Setup Guide](setup.md)

---

*Last Updated: November 7, 2025*

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

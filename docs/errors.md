# Error Handling Guide

Comprehensive guide to error handling in fs-backend.

## Overview

fs-backend uses **domain exceptions** mapped to HTTP status codes via centralized exception handlers. This separates business logic from HTTP concerns and provides consistent error responses.

**Exception Module**: `app/core/exceptions.py`  
**Handler Module**: `app/core/exception_handlers.py`

---

## Error Response Format

All errors return consistent JSON structure:

```json
{
  "detail": "Human-readable error message describing what went wrong"
}
```

**Example Errors**:
```json
{"detail": "Invalid username or password"}
{"detail": "Username must be at least 4 characters"}
{"detail": "User '550e8400-...' not found"}
```

---

## HTTP Status Codes

### Standard Error Codes

| Status | Code | Exception Type | Usage |
|--------|------|----------------|-------|
| `400` | Bad Request | `ValidationError` | Input validation failed |
| `401` | Unauthorized | `AuthenticationError` | Invalid/missing token, wrong credentials |
| `403` | Forbidden | `AuthorizationError` | Insufficient permissions |
| `404` | Not Found | `ResourceNotFoundError` | Resource doesn't exist |
| `409` | Conflict | `ResourceConflictError` | Resource already exists |
| `422` | Unprocessable Entity | Pydantic validation | Invalid request format |
| `500` | Internal Server Error | Unhandled exception | Server error (should not occur) |

---

## Exception Hierarchy

fs-backend uses a hierarchical exception structure:

```
DomainError (base)
├─ ValidationError (400)
│  ├─ Used when input doesn't meet business rules
│  └─ e.g., password < 8 characters
│
├─ AuthenticationError (401 base)
│  ├─ InvalidCredentialsError
│  │  └─ Login with wrong username/password
│  ├─ InvalidTokenError
│  │  └─ Token malformed or tampered
│  ├─ TokenExpiredError
│  │  └─ Token expired
│  ├─ TokenRevokedError
│  │  └─ Token version mismatch (after logout/password change)
│  └─ UserNotAuthenticatedError
│     └─ User deleted but token still valid
│
├─ AuthorizationError (403)
│  └─ UserNotAuthorizedError
│     └─ User lacks permission for operation
│
├─ ResourceNotFoundError (404)
│  ├─ UserNotFoundError
│  │  └─ User by ID or username not found
│  └─ EmployeeNotFoundError
│     └─ Employee profile not found
│
└─ ResourceConflictError (409)
   └─ UserAlreadyExistsError
      └─ Username already exists in database
```

---

## Common Error Scenarios

### Authentication Errors

#### "Invalid username or password" (401)
**Cause**: Incorrect login credentials  
**Response**:
```json
{
  "detail": "Invalid username or password"
}
```
**Action**: Verify credentials and try again

#### "Invalid authentication credentials" (401)
**Cause**: Malformed, expired, or tampered JWT token  
**Response**:
```json
{
  "detail": "Invalid authentication credentials"
}
```
**Action**: Obtain new token via `/auth/login` or `/auth/refresh`

#### "Token has been revoked" (401)
**Cause**: User changed password or logged out all sessions  
**Response**:
```json
{
  "detail": "Token has been revoked"
}
```
**Action**: Re-authenticate with current credentials

#### "User not found" (401)
**Cause**: User deleted but token still valid  
**Response**:
```json
{
  "detail": "User not found"
}
```
**Action**: Contact administrator

### Validation Errors

#### "Username must be at least 4 characters" (400/422)
**Cause**: Username too short  
**Response**:
```json
{
  "detail": "Username must be at least 4 characters"
}
```
**Rules**: 
- Minimum 4 characters
- No whitespace
- Must be unique

#### "Password must be at least 8 characters" (400/422)
**Cause**: Password too short  
**Response**:
```json
{
  "detail": "Password must be at least 8 characters"
}
```
**Rules**: Minimum 8 characters

#### "New password must differ from current password" (400)
**Cause**: Attempting to set same password  
**Response**:
```json
{
  "detail": "New password must differ from current password"
}
```
**Action**: Choose a different password

### Authorization Errors

#### "Not authorized to perform this action" (403)
**Cause**: User lacks required permissions  
**Response**:
```json
{
  "detail": "Not authorized to perform this action"
}
```
**Possible Causes**:
- Non-superuser trying to delete user
- Non-supervisor trying to manage subordinate
- Employee trying to access unrelated employee

**Action**: Request appropriate permissions or use correct account

### Resource Not Found Errors

#### "User '...' not found" (404)
**Cause**: User ID or username doesn't exist  
**Response**:
```json
{
  "detail": "User '550e8400-e29b-41d4-a716-446655440000' not found"
}
```
**Action**: Verify ID and try again

#### "Employee '...' not found" (404)
**Cause**: Employee profile doesn't exist  
**Response**:
```json
{
  "detail": "Employee '550e8400-e29b-41d4-a716-446655440000' not found"
}
```
**Action**: Create employee profile first

### Conflict Errors

#### "Username already exists" (409)
**Cause**: Attempting to register with existing username  
**Response**:
```json
{
  "detail": "Username 'john.doe' already exists"
}
```
**Action**: Choose different username

#### "Employee already exists for this user" (409)
**Cause**: User already has employee profile  
**Response**:
```json
{
  "detail": "Employee already exists for user '...'"
}
```
**Action**: Update existing employee instead of creating new

### Request Format Errors

#### Pydantic validation errors (422)
**Cause**: Malformed request body  
**Response**:
```json
{
  "detail": [
    {
      "loc": ["body", "username"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ]
}
```
**Example**: Missing required field in POST body

---

## Debugging Errors

### Enable Debug Logging

```python
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

try:
    # Your code
    pass
except Exception as e:
    logger.exception("Error occurred:")  # Logs full traceback
```

### Test Error Responses

```bash
# Invalid credentials
curl -X POST http://127.0.0.1:3001/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "wrong", "password": "wrong"}'
# Response: 401 Unauthorized

# User not found
curl http://127.0.0.1:3001/users/00000000-0000-0000-0000-000000000000 \
  -H "Authorization: Bearer <token>"
# Response: 404 Not Found

# Invalid token
curl http://127.0.0.1:3001/me \
  -H "Authorization: Bearer invalid-token"
# Response: 401 Unauthorized
```

### Parse Detailed Errors

```python
import httpx

response = httpx.get(
    "http://127.0.0.1:3001/me",
    headers={"Authorization": "Bearer invalid"}
)

if response.status_code != 200:
    error = response.json()
    print(f"Status: {response.status_code}")
    print(f"Detail: {error.get('detail', 'Unknown error')}")
```

---

## Error Handling Best Practices

### For Developers

1. **Raise appropriate exceptions**:
   ```python
   # ✓ Good: Specific exception
   if not user:
       raise UserNotFoundError(user_id=id)
   
   # ✗ Bad: Generic exception
   if not user:
       raise Exception("User not found")
   ```

2. **Include context in exceptions**:
   ```python
   # ✓ Good: Include identifying info
   raise UserNotFoundError(user_id=user_id)
   
   # ✗ Bad: No context
   raise UserNotFoundError()
   ```

3. **Validate early**:
   ```python
   # ✓ Good: Validate at API layer
   @router.post("/create")
   def create(request: UserCreate):  # Pydantic validates
       ...
   
   # ✗ Bad: Validate in service
   def create(data: dict):
       if "username" not in data:  # Should use schema
           ...
   ```

4. **Don't log sensitive data**:
   ```python
   # ✓ Good: Don't log passwords or tokens
   logger.info(f"Login attempt for user {username}")
   
   # ✗ Bad: Logs password
   logger.info(f"Login with password {password}")
   ```

### For End Users

1. **Read error messages carefully**: They describe what went wrong
2. **Check status codes**: 4xx = client error, 5xx = server error
3. **Verify input**: For 400/422 errors, check request format
4. **Check permissions**: For 403 errors, ensure you have rights
5. **Re-authenticate**: For 401 errors, get new token

---

## Troubleshooting Guide

### "500 Internal Server Error"
**Cause**: Unhandled exception in code  
**Action**:
1. Check server logs for traceback
2. Verify request format
3. Report issue if consistent

### "422 Unprocessable Entity"
**Cause**: Request body doesn't match schema  
**Action**:
1. Check Swagger docs at /docs
2. Verify field names and types
3. Ensure all required fields present
4. Check for typos

### "401 Unauthorized"
**Cause**: Missing or invalid authentication  
**Action**:
1. Verify token in Authorization header
2. Check token hasn't expired (refresh if needed)
3. Verify token format: `Authorization: Bearer <token>`
4. Re-login if persistent

### "403 Forbidden"
**Cause**: Insufficient permissions  
**Action**:
1. Verify user role (superuser vs regular)
2. Check hierarchy relationships
3. Request admin elevation if needed
4. Use different user account if appropriate

### "404 Not Found"
**Cause**: Resource doesn't exist  
**Action**:
1. Verify resource ID is correct
2. Create resource if needed
3. Check if resource was deleted
4. Verify you have view permissions

### "409 Conflict"
**Cause**: Resource already exists  
**Action**:
1. Use existing resource (don't create new)
2. Update instead of create
3. Choose different identifier

---

## Error Handling in Production

### Monitoring & Alerts

Setup alerts for:
- High rate of 401 errors (brute force attempt)
- High rate of 403 errors (permission issues)
- 500 errors (application bugs)
- Specific error patterns

### Logging

Log these details for debugging:
- Request path and method
- User ID (if authenticated)
- Error type and message
- Stack trace (on errors)
- Timestamp

**Don't log**:
- Passwords
- Tokens
- Sensitive personal data

### Rate Limiting

Consider rate limiting on:
- `/auth/login` - Prevent brute force
- `/auth/register` - Prevent spam
- `/auth/refresh` - Prevent token abuse

---

## References

- [Architecture - Exception Hierarchy](architecture.md#exception-hierarchy)
- [Authentication - Security](authentication.md#security-best-practices)
- [API - Error Responses](api-spec.md#error-responses)
- [Configuration - Logging](configuration.md)

---

*Last Updated: November 7, 2025*

**401 Unauthorized**:
```json
{
  "detail": "Invalid authentication credentials"
}
```

**404 Not Found**:
```json
{
  "detail": "User with id '123e4567-...' not found"
}
```

**409 Conflict**:
```json
{
  "detail": "Username 'johndoe' already exists"
}
```

**422 Validation Error**:
```json
{
  "detail": "Username must be at least 4 characters"
}
```

---

## Domain Exceptions

### Exception Hierarchy

**File**: `src/core/exceptions.py`

```python
class DomainError(Exception):
    """Base exception for all domain errors."""
    pass

class ValidationError(DomainError):
    """Input validation failed."""
    pass

class UserAlreadyExistsError(DomainError):
    """User with given username already exists."""
    pass

class UserNotFoundError(DomainError):
    """User not found by ID or username."""
    pass

class InvalidCredentialsError(DomainError):
    """Authentication credentials are invalid."""
    pass

class TokenDecodeError(DomainError):
    """JWT token cannot be decoded or is invalid."""
    pass
```

### When to Use Each Exception

| Exception | When to Raise | HTTP Status |
|-----------|---------------|-------------|
| `ValidationError` | Input doesn't meet business rules | 422 |
| `UserAlreadyExistsError` | Username taken during registration | 409 |
| `UserNotFoundError` | User lookup by ID fails | 404 |
| `InvalidCredentialsError` | Login with wrong password | 401 |
| `TokenDecodeError` | JWT malformed, expired, or invalid | 401 |
| `DomainError` (base) | Other business rule violations | 400 |

---

## Exception Handlers

### Centralized Mapping

**File**: `src/main.py`

```python
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from src.core.exceptions import (
    DomainError,
    InvalidCredentialsError,
    TokenDecodeError,
    UserAlreadyExistsError,
    UserNotFoundError,
    ValidationError,
)

app = FastAPI()

@app.exception_handler(UserAlreadyExistsError)
async def user_exists_handler(_, exc: UserAlreadyExistsError):
    return JSONResponse(
        status_code=409,
        content={"detail": str(exc)}
    )

@app.exception_handler(UserNotFoundError)
async def user_not_found_handler(_, exc: UserNotFoundError):
    return JSONResponse(
        status_code=404,
        content={"detail": str(exc)}
    )

@app.exception_handler(InvalidCredentialsError)
async def invalid_credentials_handler(_, exc: InvalidCredentialsError):
    return JSONResponse(
        status_code=401,
        content={"detail": str(exc)}
    )

@app.exception_handler(TokenDecodeError)
async def token_decode_handler(_, exc: TokenDecodeError):
    return JSONResponse(
        status_code=401,
        content={"detail": "Invalid authentication credentials"}
    )

@app.exception_handler(ValidationError)
async def validation_error_handler(_, exc: ValidationError):
    return JSONResponse(
        status_code=422,
        content={"detail": str(exc)}
    )

@app.exception_handler(DomainError)
async def generic_domain_error_handler(_, exc: DomainError):
    return JSONResponse(
        status_code=400,
        content={"detail": str(exc)}
    )
```

---

## Raising Exceptions

### In Services

**✅ Good Practice**:

```python
# src/services/user.py
from src.core.exceptions import UserAlreadyExistsError, ValidationError

class UserService:
    def create_user(self, data: UserCreate, session: Session) -> User:
        # Validate input
        if len(data.username) < 4:
            raise ValidationError("Username must be at least 4 characters")
        
        if ' ' in data.username:
            raise ValidationError("Username cannot contain spaces")
        
        # Check uniqueness
        existing = self.user_repo.get_by_username(data.username, session)
        if existing:
            raise UserAlreadyExistsError(
                f"Username '{data.username}' already exists"
            )
        
        # Create user...
```

**❌ Bad Practice** (don't do this):

```python
# DON'T raise HTTPException in services
from fastapi import HTTPException

def create_user(self, data: UserCreate) -> User:
    if existing:
        raise HTTPException(  # ❌ Couples service to HTTP layer
            status_code=409,
            detail="Username exists"
        )
```

### In Authentication

```python
# src/services/auth.py
from src.core.exceptions import InvalidCredentialsError, TokenDecodeError

class AuthService:
    def authenticate_user(
        self,
        username: str,
        password: str,
        session: Session
    ) -> User:
        user = self.user_repo.get_by_username(username, session)
        if not user:
            raise InvalidCredentialsError("Invalid username or password")
        
        if not verify_password(password, user.hashed_password):
            raise InvalidCredentialsError("Invalid username or password")
        
        return user
    
    def decode_token(self, token: str) -> dict:
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
            return payload
        except jwt.ExpiredSignatureError:
            raise TokenDecodeError("Token has expired")
        except jwt.InvalidTokenError:
            raise TokenDecodeError("Invalid token")
```

---

## Validation Errors

### Schema Validation (Pydantic)

FastAPI automatically validates request bodies using Pydantic schemas.

**Automatic Validation**:

```python
# src/schemas/user.py
from pydantic import BaseModel, field_validator

class UserCreate(BaseModel):
    username: str
    password: str
    
    @field_validator('username')
    @classmethod
    def validate_username(cls, v: str) -> str:
        if len(v) < 4:
            raise ValueError("Username must be at least 4 characters")
        if ' ' in v:
            raise ValueError("Username cannot contain spaces")
        return v
    
    @field_validator('password')
    @classmethod
    def validate_password(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        return v
```

**Error Response** (automatically generated by FastAPI):

```json
{
  "detail": [
    {
      "type": "value_error",
      "loc": ["body", "username"],
      "msg": "Username must be at least 4 characters",
      "input": "bob",
      "ctx": {"error": {}}
    }
  ]
}
```

### Business Logic Validation

For business rules not suitable for schema validation:

```python
# src/services/user.py
from src.core.exceptions import ValidationError

def change_password(
    self,
    user: User,
    current_password: str,
    new_password: str,
    session: Session
) -> None:
    # Verify current password
    if not verify_password(current_password, user.hashed_password):
        raise InvalidCredentialsError("Current password is incorrect")
    
    # Validate new password
    if len(new_password) < 8:
        raise ValidationError("New password must be at least 8 characters")
    
    if new_password == current_password:
        raise ValidationError("New password must be different from current")
    
    # Update password...
```

---

## Error Handling Patterns

### Try-Except in Services

**When Database Errors Occur**:

```python
from sqlalchemy.exc import IntegrityError
from src.core.exceptions import UserAlreadyExistsError

def create_user(self, data: UserCreate, session: Session) -> User:
    try:
        user = User(
            username=data.username,
            hashed_password=hash_password(data.password)
        )
        session.add(user)
        session.commit()
        session.refresh(user)
        return user
    except IntegrityError:
        session.rollback()
        # Unique constraint violation
        raise UserAlreadyExistsError(
            f"Username '{data.username}' already exists"
        )
```

### API Endpoint Error Handling

**FastAPI handles exceptions automatically**:

```python
# src/api/users.py
from fastapi import APIRouter, Depends

@router.post("/", response_model=UserRead, status_code=201)
def create_user(
    data: UserCreate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
) -> User:
    # No try-except needed!
    # Exception handlers in main.py catch domain errors
    user_service = UserService()
    return user_service.create_user(data, session)
```

---

## Common Error Scenarios

### Scenario 1: User Not Found

**Request**:
```bash
GET /users/non-existent-id
Authorization: Bearer <token>
```

**Service**:
```python
def get_user_by_id(self, user_id: str, session: Session) -> User:
    user = self.user_repo.get_by_id(user_id, session)
    if not user:
        raise UserNotFoundError(f"User with id '{user_id}' not found")
    return user
```

**Response** (404):
```json
{
  "detail": "User with id 'non-existent-id' not found"
}
```

### Scenario 2: Duplicate Username

**Request**:
```bash
POST /auth/register
{
  "username": "existinguser",
  "password": "password123"
}
```

**Service**:
```python
def register_user(self, data: UserCreate, session: Session) -> TokenPair:
    if self.user_repo.get_by_username(data.username, session):
        raise UserAlreadyExistsError(
            f"Username '{data.username}' already exists"
        )
    # Create user...
```

**Response** (409):
```json
{
  "detail": "Username 'existinguser' already exists"
}
```

### Scenario 3: Invalid Credentials

**Request**:
```bash
POST /auth/login
{
  "username": "johndoe",
  "password": "wrongpassword"
}
```

**Service**:
```python
def authenticate_user(
    self,
    username: str,
    password: str,
    session: Session
) -> User:
    user = self.user_repo.get_by_username(username, session)
    if not user or not verify_password(password, user.hashed_password):
        raise InvalidCredentialsError("Invalid username or password")
    return user
```

**Response** (401):
```json
{
  "detail": "Invalid username or password"
}
```

### Scenario 4: Expired Token

**Request**:
```bash
GET /users
Authorization: Bearer <expired-token>
```

**Dependency**:
```python
def get_current_user(token: str = Depends(oauth2_scheme)) -> User:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
    except jwt.ExpiredSignatureError:
        raise TokenDecodeError("Token has expired")
    # Validate token_version...
```

**Response** (401):
```json
{
  "detail": "Invalid authentication credentials"
}
```

**Note**: Generic message prevents information leakage about token state.

### Scenario 5: Token Version Mismatch

**Request**:
```bash
GET /users
Authorization: Bearer <token-with-old-version>
```

**Dependency**:
```python
def get_current_user(
    token: str = Depends(oauth2_scheme),
    session: Session = Depends(get_session)
) -> User:
    payload = decode_token(token)
    user = get_user_by_id(payload["sub"], session)
    
    if payload["token_version"] != str(user.token_version):
        raise TokenDecodeError("Token has been invalidated")
    
    return user
```

**Response** (401):
```json
{
  "detail": "Invalid authentication credentials"
}
```

---

## Security Considerations

### Don't Leak Information

**❌ Bad** (reveals username existence):
```python
if not user:
    raise InvalidCredentialsError("Username not found")
if not verify_password(password, user.hashed_password):
    raise InvalidCredentialsError("Password is incorrect")
```

**✅ Good** (generic message):
```python
if not user or not verify_password(password, user.hashed_password):
    raise InvalidCredentialsError("Invalid username or password")
```

### Token Error Messages

**❌ Bad** (reveals token state):
```json
{"detail": "Token expired at 2025-10-10T12:00:00"}
{"detail": "Token version mismatch: expected abc123, got def456"}
```

**✅ Good** (generic message):
```json
{"detail": "Invalid authentication credentials"}
```

### Log Detailed Errors

**Log for debugging, return generic to client**:

```python
import logging

logger = logging.getLogger(__name__)

def decode_token(self, token: str) -> dict:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        return payload
    except jwt.ExpiredSignatureError as e:
        logger.warning(f"Token expired: {e}")  # Log details
        raise TokenDecodeError("Invalid authentication credentials")  # Generic
    except jwt.InvalidTokenError as e:
        logger.warning(f"Invalid token: {e}")  # Log details
        raise TokenDecodeError("Invalid authentication credentials")  # Generic
```

---

## Testing Error Handling

### Unit Tests (Future)

```python
# tests/unit/test_auth_service.py
import pytest
from src.services.auth import AuthService
from src.core.exceptions import InvalidCredentialsError

def test_login_with_wrong_password_raises_error(test_session):
    # Setup
    service = AuthService()
    # ... create user with password "correct123" ...
    
    # Test
    with pytest.raises(InvalidCredentialsError, match="Invalid username or password"):
        service.authenticate_user("testuser", "wrong123", test_session)
```

### Integration Tests (Future)

```python
# tests/integration/test_auth_endpoints.py
def test_register_duplicate_username_returns_409(test_client):
    # Create first user
    test_client.post("/auth/register", json={
        "username": "testuser",
        "password": "password123"
    })
    
    # Try to create duplicate
    response = test_client.post("/auth/register", json={
        "username": "testuser",
        "password": "different456"
    })
    
    assert response.status_code == 409
    assert "already exists" in response.json()["detail"]
```

---

## References

- [API Specification](api-spec.md) - HTTP status codes
- [Authentication Guide](authentication.md) - Token errors
- [Development Guide](development.md) - Error handling patterns

---
*Last Updated: October 10, 2025*

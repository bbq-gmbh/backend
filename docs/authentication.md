# Authentication Guide

Comprehensive guide to the JWT-based authentication system in fs-backend.

## Overview

fs-backend uses **JWT (JSON Web Tokens)** with a **rotating token version** mechanism for stateless authentication and token invalidation.

## Authentication Flow

### 1. User Registration

```mermaid
sequenceDiagram
    Client->>API: POST /auth/register {username, password}
    API->>Service: validate & hash password
    Service->>Database: create user with token_version
    Database-->>Service: user created
    Service->>Service: issue token pair
    Service-->>API: TokenPair {access, refresh}
    API-->>Client: 200 OK + tokens
```

**Process**:
1. Client sends username and password
2. Service validates format (username ≥4 chars, password ≥8 chars)
3. Password hashed with bcrypt (cost factor 12)
4. User created with unique `token_version` UUID
5. JWT token pair issued
6. Client receives both access and refresh tokens

### 2. User Login

```mermaid
sequenceDiagram
    Client->>API: POST /auth/login {username, password}
    API->>Service: verify credentials
    Service->>Database: fetch user by username
    Database-->>Service: user data
    Service->>Service: verify password hash
    Service->>Service: issue token pair
    Service-->>API: TokenPair {access, refresh}
    API-->>Client: 200 OK + tokens
```

**Process**:
1. Client sends username and password
2. Service fetches user from database
3. Password verified using bcrypt comparison
4. If valid, JWT token pair issued
5. Tokens include user's current `token_version`

### 3. Accessing Protected Resources

```mermaid
sequenceDiagram
    Client->>API: GET /users (Authorization: Bearer <access_token>)
    API->>Dependency: extract & validate token
    Dependency->>Security: decode JWT
    Security-->>Dependency: token claims {sub, token_version, ...}
    Dependency->>Database: fetch user by ID
    Database-->>Dependency: user data
    Dependency->>Dependency: verify token_version matches
    Dependency-->>API: authenticated User object
    API->>Service: execute business logic
    Service-->>API: result
    API-->>Client: 200 OK + data
```

**Process**:
1. Client includes access token in `Authorization` header
2. Dependency extracts and decodes JWT
3. User fetched from database by `sub` claim
4. Token's `token_version` compared with user's current version
5. If match, request proceeds; otherwise 401 Unauthorized

### 4. Token Refresh

```mermaid
sequenceDiagram
    Client->>API: POST /auth/refresh {refresh_token}
    API->>Service: validate refresh token
    Service->>Security: decode refresh JWT
    Security-->>Service: token claims
    Service->>Database: fetch user
    Database-->>Service: user data
    Service->>Service: verify token_version & token_kind
    Service->>Service: issue new token pair
    Service-->>API: TokenPair {access, refresh}
    API-->>Client: 200 OK + new access and refresh tokens
```

**Process**:
1. Client sends refresh token (when access token expires)
2. Refresh token decoded and validated
3. Token kind must be "refresh"
4. Token version verified against user's current version
5. New token pair issued (both access and refresh tokens)
6. Note: Old refresh token remains valid (not invalidated)

### 5. Logout (All Devices)

```mermaid
sequenceDiagram
    Client->>API: POST /auth/logout-all (Authorization: Bearer <token>)
    API->>Dependency: authenticate user
    API->>Service: rotate_token_version(user)
    Service->>Database: update user.token_version = new UUID
    Database-->>Service: updated
    Service-->>API: success
    API-->>Client: 204 No Content
    Note over Client: All tokens now invalid
```

**Process**:
1. Client sends request with valid access token
2. Service generates new `token_version` UUID
3. User's `token_version` updated in database
4. All previously issued tokens now invalid (version mismatch)
5. User must login again on all devices

### 6. Password Change

```mermaid
sequenceDiagram
    Client->>API: POST /auth/change-password {current, new}
    API->>Dependency: authenticate user
    API->>Service: change_password(user, current, new)
    Service->>Service: verify current password
    Service->>Service: hash new password
    Service->>Service: rotate token_version
    Service->>Database: update user
    Database-->>Service: updated
    Service-->>API: success
    API-->>Client: 204 No Content
    Note over Client: Must login with new password
```

**Process**:
1. Client provides current and new passwords
2. Current password verified
3. New password hashed with bcrypt
4. `token_version` rotated (invalidates all tokens)
5. User must re-authenticate with new password

---

## JWT Token Details

### Token Structure

#### Access Token
```json
{
  "sub": "123e4567-e89b-12d3-a456-426614174000",
  "token_version": "987fcdeb-51a2-43f7-b890-123456789abc",
  "token_kind": "access",
  "iat": 1728518400,
  "exp": 1728522000
}
```

#### Refresh Token
```json
{
  "sub": "123e4567-e89b-12d3-a456-426614174000",
  "token_version": "987fcdeb-51a2-43f7-b890-123456789abc",
  "token_kind": "refresh",
  "iat": 1728518400,
  "exp": 1729123200
}
```

### Claims Explained

| Claim | Type | Description |
|-------|------|-------------|
| `sub` | string | Subject - User ID (UUID) |
| `token_version` | string | Rotating UUID for token invalidation |
| `token_kind` | string | Token type: "access" or "refresh" |
| `iat` | integer | Issued At - Unix timestamp |
| `exp` | integer | Expiration - Unix timestamp |

### Token Lifetimes

| Token Type | Lifetime | Use Case |
|------------|----------|----------|
| Access Token | 15 minutes | Short-lived, used for API requests |
| Refresh Token | 7 days | Long-lived, used to obtain new access tokens |

**Configuration** (in `.env`):
```env
ACCESS_TOKEN_EXPIRE_MINUTES=15
REFRESH_TOKEN_EXPIRE_DAYS=7
```

---

## Token Invalidation Mechanism

### The Token Version Strategy

**Problem**: JWTs are stateless and cannot be revoked without maintaining a blacklist.

**Solution**: Each user has a `token_version` field (UUID) stored in the database. This value is:
1. Embedded in every JWT issued to the user
2. Rotated when the user logs out (all devices) or changes password
3. Validated on every protected request

**When Token Version Changes**:
- User logs out from all devices → `token_version` rotated
- User changes password → `token_version` rotated
- Admin forces re-authentication → `token_version` rotated (future feature)

**Result**: All tokens with old `token_version` become immediately invalid without needing a blacklist.

### Validation Process

```python
# Pseudocode
def validate_token(token: str, user: User) -> bool:
    claims = decode_jwt(token)
    
    # Check expiration (handled by JWT library)
    if claims['exp'] < now():
        raise TokenExpiredError()
    
    # Check token version matches current user version
    if claims['token_version'] != user.token_version:
        raise TokenInvalidatedError()
    
    return True
```

---

## Password Security

### Hashing Algorithm

**Algorithm**: bcrypt with cost factor 12

**Why bcrypt?**
- Adaptive: cost factor can be increased as hardware improves
- Salted: unique hash for identical passwords
- Slow: resistant to brute-force attacks

**Code Reference**:
```python
# src/core/security.py
import bcrypt

def hash_password(password: str) -> str:
    return bcrypt.hashpw(
        password.encode('utf-8'),
        bcrypt.gensalt()
    ).decode('utf-8')

def verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(
        plain.encode('utf-8'),
        hashed.encode('utf-8')
    )
```

### Password Requirements

**Current Rules**:
- Minimum length: 8 characters
- No complexity requirements (for MVP)

**Future Enhancements**:
- Require uppercase, lowercase, number, special character
- Check against common password lists
- Implement password strength meter
- Prevent password reuse (store password history)

---

## Security Best Practices

### Client-Side

#### ✅ DO:
- Store tokens securely (HttpOnly cookies preferred, or secure localStorage)
- Send access token in `Authorization` header: `Bearer <token>`
- Refresh access token before expiration
- Clear tokens on logout
- Implement token refresh logic before expiry

#### ❌ DON'T:
- Store tokens in plain cookies without HttpOnly flag
- Store tokens in localStorage if XSS risk is high
- Send tokens in URL query parameters
- Store refresh tokens in easily accessible locations

### Server-Side (Current Implementation)

#### ✅ Implemented:
- Password hashing with bcrypt
- Token expiration enforcement
- Token version validation
- HTTPS enforcement (production)
- No sensitive data in JWT payload

#### ⏳ Future Security Enhancements:
- **Rate Limiting**: Prevent brute force attacks
  - Login endpoint: 5 attempts per minute per IP
  - API endpoints: 100 requests per minute per user
- **Refresh Token Rotation**: Issue new refresh token on each use
- **IP/Device Tracking**: Detect suspicious login locations
- **CORS Configuration**: Restrict allowed origins in production
- **Request ID Tracing**: Track requests across logs
- **Account Lockout**: Temporarily disable account after failed attempts

---

## Common Authentication Scenarios

### Scenario 1: User Session Lifecycle

```bash
# 1. Login
LOGIN_RESPONSE=$(curl -s -X POST http://127.0.0.1:3001/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "alice", "password": "password123"}')

ACCESS=$(echo $LOGIN_RESPONSE | jq -r '.access_token')
REFRESH=$(echo $LOGIN_RESPONSE | jq -r '.refresh_token')

# 2. Use access token (valid for 15 minutes)
curl -X GET http://127.0.0.1:3001/users \
  -H "Authorization: Bearer $ACCESS"

# 3. After 15 minutes, refresh the access token
NEW_TOKEN=$(curl -s -X POST http://127.0.0.1:3001/auth/refresh \
  -H "Content-Type: application/json" \
  -d "{\"refresh_token\": \"$REFRESH\"}" | jq -r '.access_token')

# 4. Continue using new access token
curl -X GET http://127.0.0.1:3001/users \
  -H "Authorization: Bearer $NEW_TOKEN"

# 5. Logout from all devices
curl -X POST http://127.0.0.1:3001/auth/logout-all \
  -H "Authorization: Bearer $NEW_TOKEN"
```

### Scenario 2: Handling Token Expiration

```javascript
// JavaScript client example
async function apiCall(endpoint) {
  let accessToken = localStorage.getItem('access_token');
  
  let response = await fetch(endpoint, {
    headers: { 'Authorization': `Bearer ${accessToken}` }
  });
  
  if (response.status === 401) {
    // Token expired, try refreshing
    const refreshToken = localStorage.getItem('refresh_token');
    const refreshResponse = await fetch('/auth/refresh', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ refresh_token: refreshToken })
    });
    
    if (refreshResponse.ok) {
      const data = await refreshResponse.json();
      localStorage.setItem('access_token', data.access_token);
      
      // Retry original request
      return apiCall(endpoint);
    } else {
      // Refresh failed, redirect to login
      window.location.href = '/login';
    }
  }
  
  return response;
}
```

### Scenario 3: Forced Re-authentication

```bash
# Admin forces user re-authentication by changing password
curl -X POST http://127.0.0.1:3001/auth/change-password \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"current_password": "oldpass", "new_password": "newpass123"}'

# User's old tokens immediately invalid
curl -X GET http://127.0.0.1:3001/users \
  -H "Authorization: Bearer $OLD_TOKEN"
# Returns: 401 Unauthorized

# User must login with new credentials
curl -X POST http://127.0.0.1:3001/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "alice", "password": "newpass123"}'
```

---

## Error Handling

### Authentication Errors

| Error | Status | Cause | Solution |
|-------|--------|-------|----------|
| Invalid credentials | 401 | Wrong username/password | Check credentials |
| Token expired | 401 | Access token TTL exceeded | Use refresh token |
| Invalid token | 401 | Malformed/corrupted JWT | Re-authenticate |
| Token invalidated | 401 | Token version mismatch | Re-authenticate |
| Missing token | 401 | No Authorization header | Include token |
| Wrong token kind | 401 | Used access token for refresh | Use correct token type |

### Example Error Responses

```json
// Invalid credentials
{
  "detail": "Invalid authentication credentials"
}

// Token version mismatch (after logout/password change)
{
  "detail": "Invalid authentication credentials"
}

// Missing Authorization header
{
  "detail": "Not authenticated"
}
```

---

## Testing Authentication

### Manual Testing with curl

```bash
# Test registration
curl -v -X POST http://127.0.0.1:3001/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username": "testuser", "password": "testpass123"}'

# Test login
curl -v -X POST http://127.0.0.1:3001/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "testuser", "password": "testpass123"}'

# Test protected endpoint (replace with actual token)
curl -v -X GET http://127.0.0.1:3001/users \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."

# Test token refresh
curl -v -X POST http://127.0.0.1:3001/auth/refresh \
  -H "Content-Type: application/json" \
  -d '{"refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."}'
```

### Unit Testing (Future)

```python
# tests/unit/test_auth_service.py
def test_token_version_rotation_invalidates_tokens():
    # Create user
    user = create_test_user()
    
    # Issue tokens
    tokens = auth_service.issue_token_pair(user)
    
    # Verify tokens work
    assert auth_service.validate_access_token(tokens.access_token)
    
    # Rotate version
    auth_service.rotate_token_version(user)
    
    # Verify old tokens no longer work
    with pytest.raises(TokenInvalidatedError):
        auth_service.validate_access_token(tokens.access_token)
```

---

## References

- [API Specification](api-spec.md) - Endpoint details
- [Error Handling](errors.md) - Error codes and responses
- [Configuration](configuration.md) - Token expiration settings

---
*Last Updated: October 10, 2025*

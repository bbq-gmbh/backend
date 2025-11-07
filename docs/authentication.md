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

### Rotating Token Key Strategy

Instead of maintaining a token blacklist (which requires Redis or database lookup), fs-backend uses a **rotating token version** stored on the User model.

**How it works**:
1. Each User has a `token_key` UUID field
2. When a token is issued, the current `token_key` value is embedded in the JWT
3. On every token validation:
   ```python
   user = db.get_user_by_id(token.sub)
   if token.key != user.token_key:
       raise TokenRevokedError()  # Token is revoked
   ```
4. To invalidate all tokens, rotate the key:
   ```python
   user.token_key = uuid.uuid4()
   db.commit()
   ```

**When tokens are invalidated**:
- User calls `POST /auth/logout-all` → all tokens revoked
- User changes password via `POST /auth/change-password` → all tokens revoked
- Admin remotely revokes user session

**Advantages**:
- ✅ No external state (Redis) required
- ✅ Stateless architecture maintained
- ✅ O(1) validation (just a UUID comparison)
- ✅ Atomic operation (single database update)
- ✅ No token blacklist management

### Remote Logout & Password Reset

**Remote Logout All**:
```python
@router.post("/remote-logout-all")
def remote_logout_all(
    current_user: CurrentUserDep,  # Admin
    request: RemoteLogoutAllRequest,  # { user_id: UUID }
    user_service: UserServiceDep,
):
    # Admin invalidates all sessions for a user
    user_service.remote_logout_all(current_user, request)
    # Rotates target user's token_key
```

**Remote Reset Password**:
```python
@router.post("/remote-reset-password")
def remote_reset_password(
    current_user: CurrentUserDep,  # Admin
    request: RemoteResetPasswordRequest,  # { user_id: UUID }
    user_service: UserServiceDep,
) -> RemoteResetPasswordResponse:
    # Admin resets password, returns temporary password
    new_password = user_service.remote_reset_password(current_user, request)
    return RemoteResetPasswordResponse(temporary_password=new_password)
```

---

## Authorization: Role-based Access Control

fs-backend implements **Role-based Access Control (RBAC)** with two role levels:

### 1. Superuser Role

**Characteristics**:
- `user.is_superuser == True`
- Typically administrators or system operators
- Unrestricted access to all resources

**Permissions**:
```
✓ View all users and employees
✓ Create, update, delete any user
✓ Create, update, delete employees
✓ Manage time entries for any employee
✓ Manage absence entries for any employee
✓ Access setup endpoints
✓ Remote logout users
✓ Remote reset passwords
```

### 2. Regular User Role

**Characteristics**:
- `user.is_superuser == False`
- May or may not have an associated employee profile

**Permissions (Non-Employee User)**:
```
✓ View own profile (/me)
✓ Change own password
✗ Cannot view other users
✗ Cannot create employees
✗ Cannot manage time entries
```

**Permissions (Employee User with Supervisor)**:
```
✓ View own profile (/me)
✓ View own employee profile
✓ Change own password
✓ Create time entries for self
✓ Create absence entries for self
✓ View own time/absence entries
✓ Create time entries for subordinates
✓ Create absence entries for subordinates
✓ View subordinate employee profiles
✓ View subordinate time/absence entries
✗ Cannot view unrelated employees
```

### Authorization Check Patterns

**Pattern 1: Superuser Guard**:
```python
def delete_user(user: User, target_id: UUID):
    if not user.is_superuser:
        raise UserNotAuthorizedError()
    # Perform deletion
```

**Pattern 2: Hierarchy Check**:
```python
def create_time_entry_for_employee(
    actor: User, employee_id: UUID, entry: TimeEntryCreate
):
    target_employee = get_employee_by_id(employee_id)
    
    if actor.is_superuser:
        # Superusers can create for anyone
        return create_entry(target_employee, entry)
    
    if not actor.employee:
        raise UserNotAuthorizedError()
    
    # Check if actor supervises target
    if not is_supervisor_of(actor.employee, target_employee):
        raise UserNotAuthorizedError()
    
    return create_entry(target_employee, entry)
```

**Pattern 3: Visibility Check**:
```python
def get_user_info(actor: User, user_id: UUID):
    target_user = get_user_by_id(user_id)
    
    if actor.is_superuser:
        return target_user  # Superusers see all
    
    # Non-superusers can only see employees
    if not target_user.employee:
        raise UserNotAuthorizedError()
    
    # And only if in their hierarchy
    if actor.employee and is_supervisor_of(actor.employee, target_user.employee):
        return target_user
    
    raise UserNotAuthorizedError()
```

---

## Authorization Endpoints

### Remote Logout All Sessions

**Purpose**: Admin invalidates all sessions for a user (e.g., employee leaves company)

```bash
curl -X POST http://127.0.0.1:3001/auth/remote-logout-all \
  -H "Authorization: Bearer <admin_token>" \
  -H "Content-Type: application/json" \
  -d '{"user_id": "550e8400-e29b-41d4-a716-446655440000"}'
```

**Response**: `204 No Content`

### Remote Reset Password

**Purpose**: Admin resets password and receives temporary password

```bash
curl -X POST http://127.0.0.1:3001/auth/remote-reset-password \
  -H "Authorization: Bearer <admin_token>" \
  -H "Content-Type: application/json" \
  -d '{"user_id": "550e8400-e29b-41d4-a716-446655440000"}'
```

**Response**:
```json
{
  "temporary_password": "Tr0pic@lWxY9#Kp2"
}
```

User then logs in with username + temporary password and must change it.

---

## Password Policy

### Creation & Update Rules

**Username**:
- Minimum 4 characters
- No whitespace allowed
- Must be unique

**Password**:
- Minimum 8 characters
- Must contain uppercase, lowercase, digits, punctuation (on generation)
- No reuse of current password

**Implementation**:
```python
@staticmethod
def _validate_password(password: str):
    if not password:
        raise ValidationError("Password cannot be empty")
    if len(password) < 8:
        raise ValidationError("Password must be at least 8 characters")

# On change:
if current_password == new_password:
    raise ValidationError("New password must differ from current")
```

### Secure Password Generation

```python
def generate_secure_password_with_requirements(length: int = 16) -> str:
    """Generates random password with uppercase, lowercase, digits, punctuation"""
    # Ensures at least one of each type
    password = [
        secrets.choice(string.ascii_lowercase),
        secrets.choice(string.ascii_uppercase),
        secrets.choice(string.digits),
        secrets.choice(string.punctuation),
    ]
    
    # Fill remainder randomly
    characters = string.ascii_letters + string.digits + string.punctuation
    password += [secrets.choice(characters) for _ in range(length - 4)]
    
    # Shuffle to avoid predictable pattern
    secrets.SystemRandom().shuffle(password)
    
    return "".join(password)
```

Used for admin-initiated password resets.

---

## Security Best Practices

### For Developers

1. **Never log tokens**: Don't include tokens in logs or error messages
   ```python
   # ✗ BAD
   logger.info(f"Token received: {token}")
   
   # ✓ GOOD
   logger.info("Token received and validated")
   ```

2. **Validate early**: Validate input at API layer
   ```python
   # Pydantic automatically validates request bodies
   def login(request: LoginRequest):  # Validates username/password
       ...
   ```

3. **Use strong secrets**: Generate 32+ character random secrets
   ```bash
   python -c "import secrets; print(secrets.token_urlsafe(32))"
   ```

4. **Rotate secrets regularly**: Change JWT_SECRET_KEY periodically
   - Invalidates old tokens on next rotation
   - Use a key management system in production

5. **Audit admin actions**: Log all remote operations
   - Who: Admin user ID
   - What: Remote logout/password reset
   - When: Timestamp
   - Target: User ID affected

### For Administrators

1. **Protect .env file**: Never commit to version control
   ```bash
   echo ".env" >> .gitignore
   chmod 600 .env  # Read-only for owner
   ```

2. **Use strong JWT_SECRET_KEY**: At least 32 random characters
   - Not a password or default value
   - Different for each environment
   - Stored securely (secrets manager, .env, environment variable)

3. **Enforce HTTPS in production**: Always use TLS/SSL
   - Prevents token interception
   - Use certificates from trusted CAs
   - Configure HSTS headers

4. **Implement rate limiting**: On authentication endpoints
   ```
   /auth/login - Max 5 failed attempts per 15 minutes
   /auth/register - Max 10 per hour per IP
   /auth/refresh - Max 100 per hour per user
   ```

5. **Monitor token usage**: Alert on suspicious patterns
   - Same user token used from multiple IPs simultaneously
   - Unusual time entry modifications
   - Frequent password changes

6. **Regular password audits**: Check for weak or default passwords
   - Force password change for inactive users
   - Implement password expiry if required

### For End Users

1. **Keep tokens private**: Don't share tokens in chat/email
2. **Use logout**: Always logout when done, especially on shared devices
3. **Monitor active sessions**: Use `/auth/logout-all` if suspicious activity
4. **Change password regularly**: Update password every 90 days recommended
5. **Report suspicious activity**: To administrators immediately

---

## Troubleshooting

### "Invalid authentication credentials"
**Cause**: Bearer token is invalid, expired, or revoked
**Solutions**:
1. Check token format: `Authorization: Bearer <token>`
2. Use `/auth/refresh` to get new token
3. Re-login if token expired: `/auth/login`

### "Token has been revoked"
**Cause**: User changed password or logged out all devices
**Solutions**:
1. Re-login with current credentials
2. Request password reset from admin

### "Not authorized to perform this action"
**Cause**: User lacks required permissions
**Solutions**:
1. Check user role (superuser? employee?)
2. Check hierarchy relationship (supervisor?)
3. Request admin to grant permissions

### "User not found"
**Cause**: User deleted after token was issued
**Solutions**:
1. Contact administrator
2. Create new account and re-login

---

*Last Updated: November 7, 2025*### The Token Version Strategy

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

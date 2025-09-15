# Backend Application Specification

## Overview

This document outlines the architecture and implementation requirements for transforming our FastAPI **PUT /users/password**
- Change current user's password
- Headers: `Authorization: Bearer <token>`
- Input: `{ "current_password": "string", "new_password": "string" }`
- Output: `{ "message": "Password changed successfully" }`
- Note: Generates new validation key, invalidating all existing tokenstype into a production-ready backend application. The system provides user management capabilities with JWT-based authentication.

## Technology Stack

### Core Technologies
- **Framework**: FastAPI (Python 3.13+)
- **ORM**: SQLModel (for database management)
- **Authentication**: JWT Bearer Tokens
- **Database**: PostgreSQL (production) / SQLite (development)
- **Package Management**: uv

### Dependencies
- `bcrypt>=4.3.0`,
- `fastapi[standard]>=0.116.1`,
- `pyjwt>=2.10.1`,
- `sqlmodel>=0.0.24`,

## Architecture

### Layer Structure

```
src/
├── main.py                 # FastAPI application entry point
├── config/
│   ├── __init__.py
│   ├── settings.py         # Environment configuration
│   └── database.py         # Database connection setup
├── models/
│   ├── __init__.py
│   ├── user.py            # User SQLModel models
│   └── base.py            # Base model classes
├── schemas/
│   ├── __init__.py
│   ├── user.py            # Pydantic request/response schemas
│   └── auth.py            # Authentication schemas
├── services/
│   ├── __init__.py
│   ├── user.py            # User business logic
│   └── auth.py            # Authentication service
├── repositories/
│   ├── __init__.py
│   ├── base.py            # Base repository pattern
│   └── user.py            # User data access layer
├── api/
│   ├── __init__.py
│   ├── users.py           # User endpoints
│   ├── auth.py            # Authentication endpoints
│   └── dependencies.py    # FastAPI dependencies
└── core/
    ├── __init__.py
    ├── security.py        # JWT and password utilities
    └── exceptions.py      # Custom exception handlers
```

### Application Layers

1. **API Layer** (`api/`): FastAPI route handlers and request/response handling
2. **Service Layer** (`services/`): Business logic and application rules
3. **Repository Layer** (`repositories/`): Data access abstraction
4. **Model Layer** (`models/`): SQLModel database models
5. **Schema Layer** (`schemas/`): Pydantic request/response validation

## Database Design

### User Model
```python
class User(SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    username: str = Field(unique=True, index=True)
    password_hash: str
    validation_key: str = Field(default_factory=lambda: str(uuid.uuid4()))
    is_active: bool = Field(default=True)
    is_superuser: bool = Field(default=False)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
```


## API Specification

### Authentication

#### JWT Token Structure
```json
{
  "user_id": "uuid",
  "validation_key": "user_specific_key",
  "exp": "timestamp",
  "iat": "timestamp"
}
```

#### Protected Endpoints
All endpoints except registration and login require `Authorization: Bearer <token>` header.

### Endpoints

#### Authentication Endpoints

**POST /auth/register**
- Create new user account
- Input: `{ "username": "string", "password": "string" }`
- Output: `{ "user": UserResponse, "access_token": "string", "refresh_token": "string", "token_type": "bearer" }`

**POST /auth/login**
- User login
- Input: `{ "username": "string", "password": "string" }`
- Output: `{ "access_token": "string", "refresh_token": "string", "token_type": "bearer" }`

**POST /auth/refresh**
- Refresh access token using refresh token
- Input: `{ "refresh_token": "string" }`
- Output: `{ "access_token": "string", "token_type": "bearer" }`

**POST /auth/logout-all**
- Logout from all devices (invalidate all user tokens)
- Headers: `Authorization: Bearer <token>`
- Output: `{ "message": "Successfully logged out from all devices" }`
- Note: Generates new validation key, invalidating all user tokens

#### User Management Endpoints

**POST /users**
- Create new user (admin only)
- Headers: `Authorization: Bearer <token>`
- Input: `{ "username": "string", "password": "string" }`
- Output: `UserResponse`

**DELETE /users/{user_id}**
- Delete user account (admin only)
- Headers: `Authorization: Bearer <token>`
- Output: `{ "message": "User deleted successfully" }`
- Note: Only admin users can delete accounts

**PUT /users/password**
- Change current user's password
- Headers: `Authorization: Bearer <token>`
- Input: `{ "current_password": "string", "new_password": "string" }`
- Output: `{ "message": "Password changed successfully" }`

## Security Requirements

### Password Security
- Use bcrypt for password hashing
- Minimum password requirement: 8 characters
- Salt rounds: 12

### JWT Security
- Use HS256 algorithm with secret key
- Access token expiry: 30 minutes
- Refresh token expiry: 7 days
- Both access and refresh tokens contain the same `validation_key`
- Refresh tokens validated by checking validation key against user's current validation key
- Token invalidation: Change user's validation key in database (invalidates both access and refresh tokens)
- Logout all devices: Generate new validation key for user
- Password change: Generate new validation key (invalidates all tokens)

### Environment Variables
```bash
# Database
DATABASE_URL=postgresql://user:password@localhost/dbname

# JWT Security
JWT_SECRET_KEY=your-secret-key
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# Application
APP_NAME=fs-backend
DEBUG=false
CORS_ORIGINS=["http://localhost:3000"]
```

## Error Handling

### HTTP Status Codes
- `200` - Success
- `201` - Created
- `204` - No Content
- `400` - Bad Request
- `401` - Unauthorized
- `403` - Forbidden
- `404` - Not Found
- `422` - Validation Error
- `500` - Internal Server Error

### Error Response Format
```json
{
  "detail": "Error message",
  "error_code": "SPECIFIC_ERROR_CODE",
  "timestamp": "2025-09-15T10:30:00Z"
}
```

## Deployment & Operations

### Docker Configuration
```dockerfile
FROM python:3.13-slim
WORKDIR /app
COPY pyproject.toml uv.lock ./
RUN pip install uv && uv sync --frozen
COPY src/ ./src/
EXPOSE 8000
CMD ["uv", "run", "fastapi", "run", "src/main.py", "--host", "0.0.0.0", "--port", "8000"]
```

### Health Checks
- `/health` endpoint for basic health check
- `/health/db` endpoint for database connectivity check

### Logging
- Structured logging with JSON format
- Log levels: DEBUG, INFO, WARNING, ERROR, CRITICAL
- Request/response logging for audit trails

### Monitoring
- Application metrics collection
- Database connection monitoring
- JWT token usage tracking

## Migration from Prototype

### Phase 1: Foundation
1. Implement proper project structure
2. Add SQLModel with PostgreSQL
3. Implement proper password hashing
4. Add environment configuration

### Phase 2: Security Enhancement
1. Upgrade JWT implementation
2. Add proper error handling
3. Implement input validation
4. Add CORS configuration

### Phase 3: Production Readiness
1. Implement logging and monitoring
2. Container deployment setup

### Phase 4: Advanced Features
1. Add refresh token mechanism
2. Implement role-based access control
3. Add API rate limiting
4. Performance optimization

## Development Guidelines

### Code Quality
- Follow PEP 8 style guidelines
- Use type hints throughout
- Use pre-commit hooks for code formatting

### Git Workflow
- Feature branch development
- Pull request reviews
- Automated CI/CD pipeline
- Semantic versioning

### Documentation
- API documentation via FastAPI's automatic OpenAPI
- Code documentation with docstrings
- Architecture decision records (ADRs)
- Deployment runbooks
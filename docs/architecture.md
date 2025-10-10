# Architecture Overview

## System Design

fs-backend is a lightweight FastAPI-based authentication and user management service following a clean, layered architecture.

## Technology Stack

- **Framework**: FastAPI 0.116+
- **ORM**: SQLModel 0.0.24
- **Database**: SQLite (dev), PostgreSQL-ready
- **Authentication**: JWT (PyJWT) with bcrypt password hashing
- **Python**: 3.13+
- **Package Manager**: uv

## Architectural Layers

```
┌─────────────────────────────────────┐
│         API Layer (Routers)         │  ← HTTP interface, request validation
├─────────────────────────────────────┤
│      Service Layer (Business)       │  ← Business logic, orchestration
├─────────────────────────────────────┤
│    Repository Layer (Data Access)   │  ← Database queries, data mapping
├─────────────────────────────────────┤
│       Models & Schemas (Domain)     │  ← Domain entities, DTOs
├─────────────────────────────────────┤
│    Infrastructure (DB, Config)      │  ← Technical concerns
└─────────────────────────────────────┘
```

### Layer Responsibilities

#### 1. API Layer (`src/api/`)
- **Purpose**: HTTP request/response handling
- **Responsibilities**:
  - Route definitions
  - Request validation (via Pydantic schemas)
  - Dependency injection setup
  - Response serialization
- **Key Files**:
  - `auth.py` - Authentication endpoints
  - `users.py` - User management endpoints
  - `dependencies.py` - Shared dependencies (DB session, current user)

#### 2. Service Layer (`src/services/`)
- **Purpose**: Business logic and workflow orchestration
- **Responsibilities**:
  - Enforce business rules
  - Coordinate multiple repository operations
  - Raise domain exceptions
  - Transaction management (commit/rollback)
- **Key Files**:
  - `auth.py` - Token issuance, validation, password changes
  - `user.py` - User creation, retrieval, validation

#### 3. Repository Layer (`src/repositories/`)
- **Purpose**: Data access abstraction
- **Responsibilities**:
  - Database queries
  - Entity persistence
  - Data retrieval patterns
  - **Note**: Does NOT commit transactions (service layer responsibility)
- **Key Files**:
  - `user.py` - User-specific queries

#### 4. Domain Layer

##### Models (`src/models/`)
- **Purpose**: Database entity definitions
- **Technology**: SQLModel (combines Pydantic + SQLAlchemy)
- **Key Files**:
  - `user.py` - User entity with authentication fields
  - `employee.py` - Employee entity (future use)

##### Schemas (`src/schemas/`)
- **Purpose**: Data Transfer Objects (DTOs)
- **Responsibilities**:
  - Input validation
  - Output serialization
  - API contracts
- **Key Files**:
  - `user.py` - UserCreate, UserRead
  - `auth.py` - TokenPair, LoginRequest, PasswordChangeRequest

#### 5. Core (`src/core/`)
- **Purpose**: Cross-cutting concerns
- **Key Files**:
  - `exceptions.py` - Domain exception hierarchy
  - `security.py` - JWT encoding/decoding, password hashing

#### 6. Config (`src/config/`)
- **Purpose**: Application configuration and infrastructure
- **Key Files**:
  - `settings.py` - Environment variable loading
  - `database.py` - Database engine and session factory

## Key Design Decisions

### 1. Token Invalidation Strategy
**Rotating Token Version**: Each user has a `token_version` field (UUID). This value is embedded in JWT tokens. When a user logs out (all devices) or changes password, the `token_version` is rotated, invalidating all previously issued tokens.

**Rationale**: Simple, stateless invalidation without token blacklisting or Redis dependency.

### 2. Synchronous Database Access
**Choice**: Sync SQLModel/SQLAlchemy instead of async.

**Rationale**: 
- Simpler mental model for MVP
- SQLite doesn't benefit from async I/O
- Easy migration to async later if needed
- Most operations are I/O bound on external calls, not DB

### 3. Repository Commit Removal
**Pattern**: Repositories do not commit; services control transactions.

**Benefits**:
- Enables atomic multi-entity operations
- Clear transaction boundaries
- Easier testing (can rollback in tests)

### 4. Domain Exception Mapping
**Pattern**: Services raise domain exceptions (`UserNotFoundError`, `InvalidCredentialsError`), centralized handlers in `main.py` map to HTTP status codes.

**Benefits**:
- Business logic isolated from HTTP concerns
- Consistent error responses
- Easy to change status codes without touching services

### 5. JWT Claims Structure
```json
{
  "sub": "user-id-uuid",
  "token_version": "uuid-matching-user-token-version",
  "token_kind": "access | refresh",
  "iat": 1728518400,
  "exp": 1728522000
}
```

**Key Points**:
- `sub` (subject): Standard JWT claim for user ID
- `token_version`: Enables token invalidation
- `token_kind`: Distinguishes access vs refresh tokens
- Timestamps as integers for interoperability

## Data Flow Examples

### User Registration Flow
```
1. POST /auth/register {username, password}
2. API validates input (schema)
3. AuthService.register_user()
   a. Check username uniqueness (via UserRepository)
   b. Hash password (bcrypt)
   c. Create user entity
   d. Repository adds to session
   e. Service commits transaction
4. AuthService.issue_token_pair()
   a. Generate access token (15 min)
   b. Generate refresh token (7 days)
5. Return TokenPair response
```

### Protected Endpoint Access
```
1. GET /users (Authorization: Bearer <token>)
2. Dependency: get_current_user()
   a. Extract token from header
   b. Decode JWT (security.decode_token)
   c. Validate token_version matches user.token_version
   d. Return User object
3. UserService.get_all_users()
4. Return UserRead[] response
```

### Token Rotation (Logout All)
```
1. POST /auth/logout-all
2. Dependency: get_current_user() verifies caller
3. AuthService.rotate_token_version()
   a. Generate new UUID for user.token_version
   b. Update user entity
   c. Commit transaction
4. All existing tokens now invalid (version mismatch)
```

## Security Considerations

### Implemented
- ✅ Password hashing with bcrypt (cost factor 12)
- ✅ JWT with expiration (short access, longer refresh)
- ✅ Token invalidation via version rotation
- ✅ Username uniqueness enforcement
- ✅ Password complexity validation (≥8 chars)
- ✅ Domain exception mapping (no sensitive error details leaked)

### Future Enhancements
- ⏳ Rate limiting (login attempts, API calls)
- ⏳ Argon2 password hashing (stronger than bcrypt)
- ⏳ Refresh token rotation (new refresh on each use)
- ⏳ CORS configuration for production
- ⏳ Request ID tracing
- ⏳ Brute force protection

## Scalability Path

### Current (MVP)
- SQLite database
- In-memory Python process
- Single server deployment

### Growth Options
1. **Database**: Migrate to PostgreSQL (SQLModel supports seamlessly)
2. **Caching**: Add Redis for token blacklisting or session data
3. **Horizontal Scaling**: 
   - Move to async database driver
   - Add load balancer
   - Share state via Redis/database
4. **Observability**: 
   - Structured logging (JSON)
   - Metrics (Prometheus)
   - Distributed tracing (OpenTelemetry)

## Project Structure
```
backend/
├── src/
│   ├── api/              # HTTP layer
│   ├── services/         # Business logic
│   ├── repositories/     # Data access
│   ├── models/           # Database entities
│   ├── schemas/          # DTOs
│   ├── core/             # Exceptions, security
│   └── config/           # Settings, DB setup
├── docs/                 # This directory
├── tests/                # Test suite (to be added)
└── main.py               # Application entry point
```

## References
- [API Specification](api-spec.md)
- [Authentication Details](authentication.md)
- [Database Schema](database.md)

---
*Last Updated: October 10, 2025*

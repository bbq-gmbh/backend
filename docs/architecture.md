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

# Architecture Overview

## System Design

fs-backend is a clean, layered FastAPI-based backend for employee time tracking and management. It follows a domain-driven design with separation of concerns across API, service, repository, and domain layers.

## Technology Stack

- **Framework**: FastAPI 0.121+ - Modern, async Python web framework
- **ORM**: SQLModel 0.0.27+ - Combines Pydantic + SQLAlchemy
- **Database**: SQLite (dev), PostgreSQL (prod)
- **Authentication**: PyJWT 2.10.1+ - JWT tokens
- **Security**: bcrypt 5.0+ - Password hashing
- **Python**: 3.13+
- **Package Manager**: uv - Fast Python package management
- **Testing**: pytest 8.4.2+ - Unit and integration tests

## Architectural Layers

```
┌─────────────────────────────────────────────────────────┐
│              FastAPI Application (main.py)              │
└─────────────────────────────────────────────────────────┘
                           │
        ┌──────────────────┼──────────────────┐
        │                  │                  │
┌───────▼────────┐  ┌──────▼────────┐  ┌─────▼──────────┐
│   API Layer    │  │ Exception     │  │ Lifespan      │
│   (Routers)    │  │ Handlers      │  │ Management    │
└───────────────┬┘  └───────────────┘  └───────────────┘
        │
        ├─ Auth Endpoints       (Login, Register, Refresh, etc.)
        ├─ User Endpoints       (CRUD, Search)
        ├─ Employee Endpoints   (Profile, Hierarchy)
        ├─ Time Entry Endpoints (Create, Query, Delete)
        └─ Absence Entry Endpoints
        
        │ Dependency Injection
        │ (dependencies.py)
        │
┌───────▼─────────────────────────────────────────────────┐
│        Service Layer (Business Logic)                   │
│  ────────────────────────────────────────────────────  │
│  ├─ AuthService      (Token issuance, validation)      │
│  ├─ UserService      (User lifecycle, auth)            │
│  ├─ EmployeeService  (Employee mgmt, hierarchy)        │
│  └─ TimeEntryService (Time & absence tracking)         │
└───────┬─────────────────────────────────────────────────┘
        │ Uses
        │
┌───────▼─────────────────────────────────────────────────┐
│       Repository Layer (Data Access)                    │
│  ────────────────────────────────────────────────────  │
│  ├─ UserRepository   (User queries)                     │
│  ├─ EmployeeRepository                                  │
│  ├─ EmployeeHierarchyRepository                         │
│  ├─ TimeEntryRepository                                 │
│  ├─ AbsenceEntryRepository                              │
│  └─ ServerStoreRepository                               │
└───────┬─────────────────────────────────────────────────┘
        │ Queries
        │
┌───────▼──────────────────────────────────────────────────┐
│         Domain Layer                                     │
│  ────────────────────────────────────────────────────  │
│  Models (SQLModel):    Schemas (Pydantic):             │
│  ├─ User             ├─ UserCreate, UserInfo, UserPatch
│  ├─ Employee         ├─ EmployeeCreate, EmployeeSchema
│  ├─ TimeEntry        ├─ TimeEntryCreate, TimeEntryGet
│  ├─ AbsenceEntry     ├─ AbsenceEntryCreate, AbsenceEntryGet
│  └─ ...              └─ TokenPair, LoginRequest, etc.
└──────┬───────────────────────────────────────────────────┘
       │
┌──────▼──────────────────────────────────────────────────┐
│     Infrastructure Layer                               │
│  ────────────────────────────────────────────────────  │
│  ├─ Database Engine & Session Factory                  │
│  ├─ Configuration (settings.py)                        │
│  ├─ Security Utils (password hashing, JWT)             │
│  └─ Exception Mapping                                  │
└───────────────────────────────────────────────────────┘
```

## Layer Responsibilities

### 1. API Layer (`app/api/`)

**Purpose**: HTTP request/response handling and routing

**Responsibilities**:
- Define route endpoints and HTTP methods
- Validate requests via Pydantic schemas
- Set up dependency injection
- Serialize responses
- Translate domain exceptions to HTTP status codes

**Key Files**:
- `api.py` - Central route registration
- `auth.py` - Authentication endpoints
- `users.py` - User management endpoints
- `employees.py` - Employee profile endpoints
- `time_entries.py` - Time tracking endpoints
- `absence_entries.py` - Absence tracking endpoints
- `me.py` - Current user profile
- `dependencies.py` - DI setup with bearer token, sessions
- `setup.py` - Admin setup endpoints
- `server_store.py` - Server configuration endpoints

**Example Endpoint**:
```python
@router.post("/login")
def login(
    login_data: LoginRequest,
    user_service: UserServiceDep,
    auth_service: AuthServiceDep,
) -> TokenPair:
    user = user_service.authenticate_user(...)
    if not user:
        raise InvalidCredentialsError()
    tokens = auth_service.issue_token_pair(user)
    return TokenPair(...)
```

### 2. Service Layer (`app/services/`)

**Purpose**: Business logic, workflows, and domain rules

**Responsibilities**:
- Implement business rules and validation
- Orchestrate multiple repository operations
- Raise domain exceptions
- Manage transactions (commit/rollback at session level)
- Enforce authorization rules

**Key Files**:
- `auth.py` - Token encoding/decoding, validation
- `user.py` - User creation, authentication, password changes
- `employee.py` - Employee CRUD, hierarchy operations
- `setup.py` - Initial system setup
- `time_entry/` - Time and absence tracking business logic

**Example Service Method**:
```python
def create_user(self, user_in: UserCreate) -> User:
    # Validate
    self._validate_username(user_in.username)
    self._validate_password(user_in.password)
    
    # Check existing
    if self.user_repo.get_user_by_username(user_in.username):
        raise UserAlreadyExistsError(user_in.username)
    
    # Persist
    user = self.user_repo.create_user(user_in)
    self.session.commit()  # Transaction boundary
    
    return user
```

### 3. Repository Layer (`app/repositories/`)

**Purpose**: Data access abstraction and query patterns

**Responsibilities**:
- Encapsulate database queries
- Provide entity persistence methods
- Map database results to domain objects
- **Do NOT commit transactions** (service layer responsibility)

**Key Files**:
- `user.py` - User queries (by ID, username, etc.)
- `employee.py` - Employee queries and relationships
- `employee_hierarchy.py` - Hierarchy traversal
- `time_entry.py` - Time entry CRUD
- `absence_entry.py` - Absence entry CRUD
- `server_store.py` - Server configuration storage

**Example Repository Method**:
```python
def create_user(self, user_in: UserCreate) -> User:
    user = User(
        username=user_in.username,
        password_hash=hash_password(user_in.password),
    )
    self.session.add(user)
    # NOTE: No commit! Service layer commits
    return user
```

### 4. Domain Layer

#### Models (`app/models/`)
**Purpose**: Database entity definitions

**Technology**: SQLModel (combines Pydantic + SQLAlchemy ORM)

**Key Entities**:
- **User** - Authentication principal
  - `id`: UUID primary key
  - `username`: Unique identifier
  - `password_hash`: Bcrypt hash
  - `token_key`: UUID for token invalidation
  - `is_superuser`: Boolean flag
  - `created_at`, `updated_at`: Timestamps
  - Relationship to Employee (optional)

- **Employee** - Employee profile with hierarchy
  - `user_id`: Foreign key to User
  - `first_name`, `last_name`: Identity
  - `birthday`: Date of birth
  - `hour_model`: HourModel enum (e30, e35, e40)
  - `pause_time_minutes`: Daily pause duration
  - `start_from`: Contract start date
  - `supervisor_id`: Optional foreign key for hierarchy
  - Relationships: supervisor, subordinates (recursive)

- **TimeEntry** - Work time tracking
  - `id`: Integer primary key
  - `user_id`: Foreign key to Employee
  - `entry_type`: TimeEntryType enum (arrival/departure)
  - `date_time`: When the entry was created
  - `created_by`: User who created entry
  - `created_at`: Timestamp

- **AbsenceEntry** - Absence tracking
  - `id`: Integer primary key
  - `user_id`: Foreign key to Employee
  - `entry_type`: AbsenceEntryType enum (sickness/vacation/other)
  - `date_begin`, `date_end`: Absence period
  - `created_by`: User who created entry
  - `created_at`: Timestamp

#### Schemas (`app/schemas/`)
**Purpose**: Data Transfer Objects and input validation

**Technology**: Pydantic v2

**Key Schemas**:
- **Auth Schemas**:
  - `LoginRequest` - Username + password
  - `TokenPair` - Access + refresh tokens
  - `TokenData` - Decoded JWT claims
  - `PasswordChangeRequest` - Current + new password

- **User Schemas**:
  - `UserCreate` - Input for creating user
  - `UserInfo` - Output user information
  - `UserPatch` - Update user data

- **Employee Schemas**:
  - `EmployeeCreate` - Input for creating employee
  - `HierarchyResponse` - Employee with supervisors/subordinates
  - `HierarchyRebuildStats` - Hierarchy repair statistics

### 5. Core Layer (`app/core/`)

**Purpose**: Cross-cutting concerns

**Responsibilities**:
- Security operations (JWT, password hashing)
- Exception hierarchy and mappings
- DateTime utilities with timezone handling
- Exception handlers (map to HTTP responses)

**Key Files**:
- `exceptions.py` - Domain exception classes
  - `AuthenticationError` - Subclass for auth errors (401)
  - `AuthorizationError` - Subclass for authorization (403)
  - `ResourceNotFoundError` - Not found errors (404)
  - `ResourceConflictError` - Conflict errors (409)
  
- `security.py` - Cryptographic operations
  - `hash_password()` - Bcrypt hashing
  - `verify_password()` - Password verification
  - `generate_secure_password_with_requirements()` - Secure generation
  
- `exception_handlers.py` - Exception to HTTP status mapping
- `datetime.py` - Date/time utilities

### 6. Config Layer (`app/config/`)

**Purpose**: Application configuration and infrastructure

**Key Files**:
- `settings.py` - Environment variable loading
  ```python
  DATABASE_URL: str
  JWT_SECRET_KEY: str
  JWT_ALGORITHM: str
  ACCESS_TOKEN_EXPIRE_MINUTES: int
  REFRESH_TOKEN_EXPIRE_DAYS: int
  ```

- `database.py` - Database engine and session factory
  - Session dependency for request scope
  - Engine initialization with URL parsing

## Key Design Patterns

### 1. Dependency Injection

**Pattern**: FastAPI's `Depends` for managing dependencies

```python
# In dependencies.py
UserServiceDep = Annotated[UserService, Depends(get_user_service)]

# In endpoint
@router.post("/login")
def login(user_service: UserServiceDep):
    # FastAPI injects service
    ...
```

**Benefits**:
- Loose coupling between layers
- Easy to mock for testing
- Single responsibility
- Clear dependency graph

### 2. Service Layer Controls Transactions

**Pattern**: Only services commit; repositories do not

```python
class UserService:
    def create_user(self, user_in: UserCreate) -> User:
        # Repository only adds to session
        user = self.user_repo.create_user(user_in)
        
        # Service commits
        self.session.commit()
        self.session.refresh(user)
        
        return user
```

**Benefits**:
- Atomic multi-entity operations
- Clear transaction boundaries
- Testable with transaction rollback
- Prevents partial state updates

### 3. Domain Exceptions Map to HTTP Responses

**Pattern**: Raise domain exceptions, centralized mapping

```python
# In service
if not user:
    raise UserNotFoundError(user_id=id)  # Domain exception

# In exception_handlers.py
@app.exception_handler(UserNotFoundError)
async def user_not_found_handler(request: Request, exc: UserNotFoundError):
    return JSONResponse(
        status_code=404,
        content={"detail": str(exc)}
    )
```

**Benefits**:
- Business logic isolated from HTTP
- Consistent error responses
- Easy to adjust status codes
- Single source of truth for error mapping

### 4. Token Invalidation Without Redis

**Pattern**: Rotating `token_key` field on User

```python
# JWT includes current token_key
payload = {
    "sub": str(user.id),
    "key": str(user.token_key),  # Current version
    "exp": ...,
    "kind": "access"
}

# On logout-all or password change
user.token_key = uuid.uuid4()  # Rotate key
session.commit()  # All previous tokens invalid

# On validation
if token.key != user.token_key:  # Mismatch
    raise TokenRevokedError()  # All tokens invalid
```

**Benefits**:
- No external state (Redis) needed
- Simple to implement and understand
- Fast validation (one comparison)
- Stateless architecture maintained

### 5. SQLModel for Models and Schemas

**Pattern**: Single definition for database + validation

```python
# Models inherit from SQLModel
class User(SQLModel, table=True):
    __tablename__ = "users"
    id: UUID = Field(primary_key=True, ...)
    username: str = Field(unique=True, index=True)
    password_hash: str
    
    # Can be used as both ORM model and Pydantic schema

# In endpoints
def create_user(user_in: UserCreate) -> UserInfo:  # Schema for validation
    user = self.user_repo.create_user(user_in)  # ORM model
    return UserInfo.model_validate(user)  # Schema for response
```

**Benefits**:
- Single source of truth
- Type safety across layers
- Validation on input and output
- Reduces boilerplate

## Data Flow Examples

### User Registration Flow

```
1. Client sends POST /auth/register {username, password}
   ├─> API Layer validates input (Pydantic schema)
   │
2. API calls UserService.create_user()
   ├─> Service validates username/password rules
   ├─> Service checks username doesn't exist
   │
3. Service calls UserRepository.create_user()
   ├─> Repository creates User entity
   ├─> Adds to session (no commit)
   │
4. Service commits transaction
   ├─> Session.commit() persists to database
   │
5. Service calls AuthService.issue_token_pair()
   ├─> Auth encodes JWT with user.id and user.token_key
   │
6. API returns TokenPair response
   ├─> Client receives {access_token, refresh_token}
```

### Authenticated Request Flow

```
1. Client sends GET /me with Authorization header
   ├─> Header: "Authorization: Bearer <access_token>"
   │
2. Dependency injection extracts bearer token
   ├─> Uses HTTPBearer security scheme
   │
3. AuthService.decode_token(token)
   ├─> Decodes JWT using SECRET_KEY
   ├─> Extracts {sub, key, exp, kind} claims
   │
4. AuthService.get_user_from_token(token_data)
   ├─> Fetches user by sub (user ID)
   ├─> Verifies token.key == user.token_key
   │
5. If valid, dependency returns authenticated User object
   │
6. Endpoint receives CurrentUserDep: User
   ├─> Can safely use user.id, user.is_superuser, etc.
   │
7. Endpoint business logic executes with authorization
   └─> Service methods check user permissions
```

### Password Change Flow

```
1. Client sends POST /auth/change-password {current, new}
   │
2. Dependency injects CurrentUserDep: User (authenticated)
   │
3. Service receives current_user and passwords
   ├─> Verifies current password against user.password_hash
   ├─> Validates new password rules (≥8 chars, different from current)
   │
4. Service hashes new password with bcrypt
   │
5. Service rotates token_key
   ├─> user.token_key = uuid.uuid4()
   │
6. Service updates user in database
   ├─> session.commit()
   │
7. All existing tokens now invalid
   ├─> Because token.key != user.token_key on next request
   │
8. Client receives 204 No Content
   └─> Must re-authenticate to get new token pair
```

## Exception Hierarchy

```
DomainError (Base)
├─ ValidationError (400)
│
├─ AuthenticationError (401 base)
│  ├─ InvalidCredentialsError
│  ├─ InvalidTokenError
│  ├─ TokenExpiredError
│  ├─ TokenRevokedError
│  └─ UserNotAuthenticatedError
│
├─ AuthorizationError (403)
│  └─ UserNotAuthorizedError
│
├─ ResourceNotFoundError (404)
│  ├─ UserNotFoundError
│  ├─ EmployeeNotFoundError
│  └─ ...
│
└─ ResourceConflictError (409)
   └─ UserAlreadyExistsError
```

## Authorization Strategy

### Role-based Access Control (RBAC)

**Superuser**:
- Can access all users and employees
- Can create, update, delete any user
- Can create, update, delete employees

**Regular User**:
- Can view own profile (`/me`)
- Can change own password
- Can view own employee profile
- Cannot view other users unless in hierarchy

**Employee with Supervisor Role**:
- Can manage time/absence entries for self
- Can manage time/absence entries for subordinates
- Can view subordinate employee profiles
- Cannot view unrelated employees

**Authorization Check Pattern**:
```python
def get_employee_hierarchy(user: User, target_employee: Employee):
    if user.is_superuser:
        # Superusers can view anyone
        return hierarchy
    
    if not user.employee:
        # Non-employee users can only view self
        if target_employee.user_id != user.id:
            raise UserNotAuthorizedError()
    else:
        # Employees can view self and subordinates
        if not employee_service.is_supervisor_of(
            user.employee, target_employee, include_self=True
        ):
            raise UserNotAuthorizedError()
    
    return hierarchy
```

## Performance Considerations

1. **Eager Loading**: Employee relationships (supervisor, subordinates) loaded eagerly to avoid N+1 queries
2. **Indexing**: Foreign keys and frequently queried fields indexed (e.g., username, user_id)
3. **Token Validation**: O(1) comparison of token_key strings
4. **Pagination**: List endpoints support page/page_size parameters
5. **Caching**: Consider caching employee hierarchy for frequently accessed supervisors

## Security Features

1. **Password Security**:
   - Bcrypt hashing with adjustable cost factor
   - Salt automatically generated per password
   - Salted hashes never exposed

2. **JWT Security**:
   - HS256 signing algorithm
   - Configurable secret key (32+ chars recommended)
   - Token versioning for revocation
   - Access tokens expire after 15 minutes
   - Refresh tokens expire after 7 days

3. **Authorization**:
   - Role-based access control (superuser flag)
   - Hierarchy-based permissions
   - Bearer token in Authorization header
   - Protected endpoints require authentication

4. **Data Protection**:
   - Parameterized queries prevent SQL injection
   - Pydantic validation prevents malformed input
   - Field validation (length, format)

## Deployment Considerations

### Development
- SQLite database (in-memory or file-based)
- Single worker
- DEBUG mode can be enabled
- `.env` file for configuration

### Production
- PostgreSQL database (scalable, robust)
- Multiple workers via gunicorn/uvicorn
- DEBUG mode disabled
- Environment variables for secrets
- HTTPS/TLS enabled
- CORS configured for frontend domain
- Rate limiting on auth endpoints
- Monitoring and logging

---

*Last Updated: November 7, 2025*
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
├── app/
│   ├── main.py                      # Application entry point (clean!)
│   ├── api/                         # HTTP layer
│   │   ├── router.py               # Route registration
│   │   ├── auth.py                 # Auth endpoints
│   │   ├── users.py                # User endpoints
│   │   └── dependencies.py         # Shared dependencies
│   ├── services/                    # Business logic
│   ├── repositories/                # Data access
│   ├── models/                      # Database entities
│   ├── schemas/                     # DTOs
│   ├── core/                        # Cross-cutting concerns
│   │   ├── exception_handlers.py  # Exception → HTTP mapping
│   │   ├── exceptions.py           # Domain exceptions
│   │   └── security.py             # JWT, passwords
│   └── config/                      # Settings, DB setup
├── docs/                            # This directory
└── tests/                           # Test suite (to be added)
```

## References
- [API Specification](api-spec.md)
- [Authentication Details](authentication.md)
- [Database Schema](database.md)

---
*Last Updated: October 10, 2025*

# Development Guide

Comprehensive guide for contributing to and developing fs-backend.

## Project Overview

**Tech Stack**: FastAPI, SQLModel, SQLite (dev), PostgreSQL (prod)  
**Python Version**: 3.13+  
**Package Manager**: uv

**Key Principles**:
- Clean, layered architecture
- Domain-driven exceptions
- Comprehensive testing
- Type safety with Python type hints
- Clear separation of concerns

---

## Development Environment Setup

### Initial Setup

```bash
# Clone repository
git clone <repository-url>
cd backend

# Install dependencies with uv
uv sync --all-groups

# Create environment file
cp .env.template .env

# Start development server
uv run fastapi dev app/main.py --port 3001
```

### Verification

```bash
# Check server is running
curl http://127.0.0.1:3001/
# Response: 200 OK

# Check Swagger docs
open http://127.0.0.1:3001/docs
```

---

## Code Organization

### Layered Architecture

```
┌─────────────────────────────────────┐
│    API Layer (app/api/)             │  HTTP handling
├─────────────────────────────────────┤
│    Service Layer (app/services/)    │  Business logic
├─────────────────────────────────────┤
│  Repository Layer (app/repositories/)  │  Data access
├─────────────────────────────────────┤
│   Domain Layer (models, schemas)    │  Entities, DTOs
├─────────────────────────────────────┤
│  Core & Config (core, config)       │  Security, settings
└─────────────────────────────────────┘
```

### File Structure

```
app/
├── main.py              # Entry point, app initialization
├── api/
│   ├── api.py           # Route registration
│   ├── auth.py          # Auth endpoints
│   ├── users.py         # User endpoints
│   ├── employees.py     # Employee endpoints
│   ├── time_entries.py  # Time tracking endpoints
│   ├── absence_entries.py
│   ├── me.py            # Current user
│   ├── dependencies.py  # DI setup
│   └── ...
├── services/
│   ├── auth.py          # Token service
│   ├── user.py          # User service
│   ├── employee.py      # Employee service
│   └── time_entry/      # Time entry services
├── repositories/
│   ├── user.py
│   ├── employee.py
│   ├── time_entry.py
│   └── ...
├── models/              # SQLModel entities
├── schemas/             # Pydantic DTOs
├── core/
│   ├── exceptions.py    # Domain exceptions
│   ├── security.py      # JWT, password utils
│   └── exception_handlers.py
└── config/
    ├── settings.py      # Environment settings
    └── database.py      # Database engine
```

---

## Development Principles

### 1. Layer Responsibilities

**API Layer** (`app/api/`):
- ✅ Handle HTTP (routes, status codes, headers)
- ✅ Validate request format (Pydantic schemas)
- ✅ Call service methods
- ✅ Return HTTP responses
- ❌ Never contain business logic
- ❌ Never directly access repositories

**Service Layer** (`app/services/`):
- ✅ Implement business logic
- ✅ Orchestrate multiple repository calls
- ✅ Enforce business rules
- ✅ Control transactions (commit/rollback)
- ✅ Raise domain exceptions
- ❌ Never return HTTP status codes
- ❌ Never access HTTP context

**Repository Layer** (`app/repositories/`):
- ✅ Database queries only
- ✅ Return entities or lists
- ✅ Provide query methods
- ❌ Never commit transactions
- ❌ Never contain business logic

### 2. Error Handling

**Use domain exceptions**, not HTTP exceptions in services:

```python
# ❌ Bad: HTTPException in service
from fastapi import HTTPException

def create_user(username: str) -> User:
    if user_exists(username):
        raise HTTPException(status_code=409, detail="Username exists")

# ✅ Good: Domain exception
from app.core.exceptions import UserAlreadyExistsError

def create_user(username: str) -> User:
    if user_exists(username):
        raise UserAlreadyExistsError(username)
```

**Mapping happens in handler**:
```python
# app/core/exception_handlers.py
@app.exception_handler(UserAlreadyExistsError)
async def user_exists_handler(request: Request, exc: UserAlreadyExistsError):
    return JSONResponse(status_code=409, content={"detail": str(exc)})
```

**Benefits**:
- Business logic isolated from HTTP
- Easy to test (no HTTP dependencies)
- Consistent error responses
- Easy to change status codes

### 3. Transaction Management

**Services control transactions**, repositories don't:

```python
# ✅ Good: Service manages commit
def create_user(data: UserCreate, session: Session) -> User:
    # Validate
    if self.user_repo.get_by_username(data.username, session):
        raise UserAlreadyExistsError()
    
    # Create
    user = User(
        username=data.username,
        password_hash=hash_password(data.password)
    )
    
    # Repository adds to session (no commit)
    self.user_repo.add(user, session)
    
    # Service commits (transaction boundary)
    session.commit()
    session.refresh(user)
    
    return user
```

**Benefits**:
- Atomic operations across multiple entities
- Testable (can rollback in tests)
- Clear transaction boundaries

### 4. Type Hints

**Use type hints everywhere**:

```python
# ✅ Good: Full type hints
from typing import Optional

def get_user_by_id(
    user_id: uuid.UUID,
    session: Session
) -> Optional[User]:
    """Retrieve user by ID."""
    return session.get(User, user_id)

# ❌ Bad: No type hints
def get_user_by_id(user_id, session):
    return session.get(User, user_id)
```

**Benefits**:
- IDE autocomplete
- Type checker support (mypy, Pylance)
- Self-documenting code
- Catches bugs early

### 5. Docstrings

**Document public functions** (Google style):

```python
def authenticate_user(
    username: str,
    password: str
) -> Optional[User]:
    """
    Authenticate user with username and password.
    
    Args:
        username: User's login name
        password: User's password (plain text)
        
    Returns:
        User object if credentials valid, None otherwise
        
    Raises:
        ValueError: If password empty or None
    """
    if not password:
        raise ValueError("Password cannot be empty")
    
    user = self.user_repo.get_by_username(username)
    if not user:
        return None
    
    if verify_password(password, user.password_hash):
        return user
    
    return None
```

---

## Testing

### Running Tests

```bash
# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=app --cov-report=html

# Run specific test file
uv run pytest tests/unit/test_user_service.py

# Run with verbose output
uv run pytest -v

# Run matching pattern
uv run pytest -k "test_create_user"
```

### Test Structure

```
tests/
├── unit/
│   ├── test_services/
│   │   └── test_auth_service.py
│   └── test_repositories/
│       └── test_employee_hierarchy.py
├── integration/
│   ├── test_auth_endpoints.py
│   └── test_user_endpoints.py
└── fixtures/
    └── user_fixtures.py
```

### Writing Tests

**Unit Test Example**:
```python
# tests/unit/test_services/test_auth_service.py
import pytest
from app.services.auth import AuthService
from app.models.user import User

def test_issue_token_pair(auth_service: AuthService, user: User):
    """Test token pair generation."""
    access_token, refresh_token = auth_service.issue_token_pair(user)
    
    assert access_token
    assert refresh_token
    assert access_token != refresh_token
```

**Integration Test Example**:
```python
# tests/integration/test_auth_endpoints.py
def test_login_success(client: TestClient):
    """Test successful login endpoint."""
    response = client.post(
        "/auth/login",
        json={"username": "testuser", "password": "testpass123"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
```

---

## Code Quality Tools

### Linting & Formatting

```bash
# Check code with Ruff
uv run ruff check app/

# Auto-fix issues
uv run ruff check --fix app/

# Format code
uv run ruff format app/
```

### Type Checking

```bash
# Check types with mypy
uv run mypy app/

# With strict mode
uv run mypy --strict app/
```

### Pre-commit Hooks

```bash
# Install pre-commit
uv add --dev pre-commit

# Configure hooks
cat > .pre-commit-config.yaml << 'EOF'
repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.1.0
    hooks:
      - id: ruff
        args: [--fix]
      - id: ruff-format
EOF

# Install hook
pre-commit install
```

---

## Adding New Features

### Example: Add Email Field to User

**1. Update Model** (`app/models/user.py`):
```python
class User(SQLModel, table=True):
    # ... existing fields ...
    email: str = Field(index=True, unique=True)
```

**2. Update Schema** (`app/schemas/user.py`):
```python
class UserCreate(SQLModel):
    username: str
    password: str
    email: str  # ← New field
```

**3. Update Service** (`app/services/user.py`):
```python
def create_user(self, user_in: UserCreate) -> User:
    self._validate_username(user_in.username)
    self._validate_password(user_in.password)
    self._validate_email(user_in.email)  # ← New validation
    
    if self.user_repo.get_by_username(user_in.username):
        raise UserAlreadyExistsError()
    
    if self.user_repo.get_by_email(user_in.email):  # ← Check unique
        raise EmailAlreadyExistsError()
    
    user = self.user_repo.create_user(user_in)
    self.session.commit()
    return user
```

**4. Update Repository** (`app/repositories/user.py`):
```python
def get_by_email(self, email: str) -> Optional[User]:
    return self.session.query(User).filter(User.email == email).first()
```

**5. Update API** (`app/api/users.py`):
```python
# UserCreate schema auto-validates new field
@router.post("/", response_model=UserInfo)
def create_user(user_in: UserCreate, user_service: UserServiceDep):
    return user_service.create_user(user_in)
```

**6. Add Tests**:
```python
def test_create_user_with_email(user_service: UserService):
    result = user_service.create_user(UserCreate(
        username="test",
        password="pass123",
        email="test@example.com"
    ))
    assert result.email == "test@example.com"
```

**7. Database Synchronization**:
```bash
# Restart server (SQLAlchemy auto-creates/updates on startup)
uv run fastapi dev app/main.py --port 3001
```

---

## Git Workflow

### Branching Strategy

```
main (production)
├── dev (development)
│   ├── feature/user-authentication
│   ├── feature/employee-hierarchy
│   └── bugfix/time-entry-validation
```

### Creating a Feature Branch

```bash
# Create and switch to new branch
git checkout -b feature/my-feature

# Make changes and test
uv run pytest

# Commit changes
git add .
git commit -m "Add: my feature description"

# Push to remote
git push origin feature/my-feature

# Create pull request on GitHub
# - Describe changes
# - Reference related issues
# - Wait for code review
```

### Commit Message Style

```
[type]: [description]

[optional body]

- [optional] Related issues: #123

Types: add, fix, refactor, docs, test, perf
```

**Examples**:
```
add: employee hierarchy endpoint
fix: token validation edge case
refactor: split user service methods
docs: update setup guide
```

---

## Debugging

### Using print/logging

```python
import logging

logger = logging.getLogger(__name__)

def create_user(data: UserCreate):
    logger.info(f"Creating user: {data.username}")
    
    try:
        user = self.user_repo.create_user(data)
        logger.info(f"User created: {user.id}")
        return user
    except Exception as e:
        logger.exception("Failed to create user")
        raise
```

### Using debugger

```python
# Add breakpoint
def authenticate_user(username: str, password: str):
    breakpoint()  # ← Stops here
    user = self.user_repo.get_by_username(username)
    # ...
```

### Using FastAPI test client

```python
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

# Test endpoint
response = client.post("/auth/login", json={
    "username": "test",
    "password": "pass"
})

print(response.status_code)
print(response.json())
```

---

## Common Development Tasks

### Adding a new endpoint

1. Create route in `app/api/module.py`
2. Create schema in `app/schemas/module.py` if needed
3. Add service method in `app/services/module.py`
4. Add repository method if database access needed
5. Add tests in `tests/integration/`
6. Run full test suite

### Modifying a model

1. Update model in `app/models/model.py`
2. Update schemas if needed
3. Update service/repository code
4. Restart server (schema auto-syncs)
5. Test thoroughly

### Fixing a bug

1. Create test that reproduces bug
2. Fix bug in code
3. Verify test passes
4. Ensure no other tests break
5. Commit with reference to issue

---

## Performance Tips

1. **Use indexes** on frequently queried fields
2. **Eager load relationships** to avoid N+1 queries
3. **Paginate list endpoints** (limit/offset)
4. **Use database LIMIT/OFFSET** not Python slicing
5. **Cache employee hierarchy** for frequently accessed supervisors

---

## Security Checklist

When adding features:
- [ ] Validate all inputs
- [ ] Check authorization (user permissions)
- [ ] Use parameterized queries (SQLModel does this)
- [ ] Don't log sensitive data
- [ ] Don't expose database errors
- [ ] Use HTTPS in production
- [ ] Encrypt sensitive data at rest

---

## Deployment

### Before Deploying

```bash
# Run full test suite
uv run pytest --cov=app

# Check code quality
uv run ruff check app/

# Type check
uv run mypy app/

# Review changes
git log --oneline -5
```

### Deployment Process

```bash
# Merge to main
git merge --no-ff feature/my-feature
git push origin main

# Build and deploy (your CI/CD pipeline)
# GitHub Actions, Docker, etc.

# Verify in production
curl https://api.example.com/
```

---

## References

- [Architecture Overview](architecture.md)
- [API Specification](api-spec.md)
- [Database Schema](database.md)
- [Error Handling](errors.md)
- [FastAPI Best Practices](https://fastapi.tiangolo.com/deployment/concepts/)
- [SQLModel Documentation](https://sqlmodel.tiangolo.com/)

---

*Last Updated: November 7, 2025*
    
    return user
```

---

## Project Structure Conventions

### File Naming
- Python files: `snake_case.py`
- Classes: `PascalCase`
- Functions/variables: `snake_case`
- Constants: `UPPER_SNAKE_CASE`

### Module Organization

```
src/
├── api/                    # HTTP layer
│   ├── __init__.py
│   ├── auth.py            # Auth endpoints
│   ├── users.py           # User endpoints
│   └── dependencies.py    # Shared dependencies
├── services/              # Business logic
│   ├── __init__.py
│   ├── auth.py
│   └── user.py
├── repositories/          # Data access
│   ├── __init__.py
│   └── user.py
├── models/                # Database entities
│   ├── __init__.py
│   ├── user.py
│   └── employee.py
├── schemas/               # Request/response DTOs
│   ├── __init__.py
│   ├── auth.py
│   └── user.py
├── core/                  # Cross-cutting concerns
│   ├── __init__.py
│   ├── exceptions.py
│   └── security.py
└── config/                # Configuration
    ├── __init__.py
    ├── settings.py
    └── database.py
```

---

## Adding New Features

### Example: Adding a New Endpoint

**Scenario**: Add endpoint to get user by ID

#### 1. Define Schema (if needed)

```python
# src/schemas/user.py
from pydantic import BaseModel
from datetime import datetime

class UserDetail(BaseModel):
    id: str
    username: str
    created_at: datetime
    updated_at: datetime
    last_login: datetime | None = None
    
    class Config:
        from_attributes = True
```

#### 2. Add Repository Method

```python
# src/repositories/user.py
from typing import Optional
from sqlmodel import Session, select
from src.models.user import User

class UserRepository:
    def get_by_id(self, user_id: str, session: Session) -> Optional[User]:
        """Fetch user by ID."""
        statement = select(User).where(User.id == user_id)
        return session.exec(statement).first()
```

#### 3. Add Service Method

```python
# src/services/user.py
from src.core.exceptions import UserNotFoundError

class UserService:
    def get_user_by_id(self, user_id: str, session: Session) -> User:
        """Get user by ID or raise exception."""
        user = self.user_repo.get_by_id(user_id, session)
        if not user:
            raise UserNotFoundError(f"User with id '{user_id}' not found")
        return user
```

#### 4. Add API Endpoint

```python
# src/api/users.py
from fastapi import APIRouter, Depends
from sqlmodel import Session
from src.api.dependencies import get_session, get_current_user
from src.services.user import UserService
from src.schemas.user import UserDetail

router = APIRouter()

@router.get("/{user_id}", response_model=UserDetail)
def get_user(
    user_id: str,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> User:
    """Get user by ID (requires authentication)."""
    user_service = UserService()
    return user_service.get_user_by_id(user_id, session)
```

#### 5. Test the Endpoint

```bash
# Register and login to get token
TOKEN=$(curl -s -X POST http://127.0.0.1:3001/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "testuser", "password": "testpass123"}' \
  | jq -r '.access_token')

# Get user by ID
curl -X GET http://127.0.0.1:3001/users/<user-id> \
  -H "Authorization: Bearer $TOKEN"
```

---

## Testing Guidelines (Future)

### Test Structure

```
tests/
├── __init__.py
├── conftest.py              # Shared fixtures
├── unit/
│   ├── test_user_service.py
│   ├── test_auth_service.py
│   └── test_security.py
└── integration/
    ├── test_auth_endpoints.py
    └── test_user_endpoints.py
```

### Test Fixtures (`conftest.py`)

```python
import pytest
from sqlmodel import Session, create_engine, SQLModel
from src.config.database import get_session
from src.main import app

@pytest.fixture
def test_engine():
    """Create in-memory SQLite for testing."""
    engine = create_engine("sqlite:///:memory:")
    SQLModel.metadata.create_all(engine)
    return engine

@pytest.fixture
def test_session(test_engine):
    """Provide test database session."""
    with Session(test_engine) as session:
        yield session

@pytest.fixture
def test_client(test_session):
    """FastAPI test client with test database."""
    def override_get_session():
        yield test_session
    
    app.dependency_overrides[get_session] = override_get_session
    from fastapi.testclient import TestClient
    return TestClient(app)
```

### Writing Tests

**Unit Test Example**:
```python
# tests/unit/test_auth_service.py
import pytest
from src.services.auth import AuthService
from src.core.exceptions import InvalidCredentialsError

def test_login_with_invalid_password(test_session):
    """Test login fails with wrong password."""
    # Setup
    service = AuthService()
    # ... create user ...
    
    # Test
    with pytest.raises(InvalidCredentialsError):
        service.authenticate_user("testuser", "wrongpassword", test_session)
```

**Integration Test Example**:
```python
# tests/integration/test_auth_endpoints.py
def test_register_creates_user(test_client):
    """Test user registration endpoint."""
    response = test_client.post(
        "/auth/register",
        json={"username": "newuser", "password": "password123"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"
```

### Running Tests

```bash
# Install test dependencies
uv add --dev pytest pytest-asyncio httpx

# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=src --cov-report=html

# Run specific test file
uv run pytest tests/unit/test_auth_service.py

# Run tests matching pattern
uv run pytest -k "test_login"
```

---

## Code Quality Tools

### Ruff (Linting & Formatting)

```bash
# Install
uv add --dev ruff

# Check code
uv run ruff check src/

# Auto-fix issues
uv run ruff check --fix src/

# Format code
uv run ruff format src/
```

**Configuration** (`pyproject.toml`):
```toml
[tool.ruff]
line-length = 88
target-version = "py313"

[tool.ruff.lint]
select = [
    "E",   # pycodestyle errors
    "W",   # pycodestyle warnings
    "F",   # pyflakes
    "I",   # isort
    "N",   # pep8-naming
    "UP",  # pyupgrade
]
ignore = []

[tool.ruff.lint.per-file-ignores]
"__init__.py" = ["F401"]  # Allow unused imports
```

### MyPy (Type Checking)

```bash
# Install
uv add --dev mypy

# Run type checker
uv run mypy src/
```

**Configuration** (`pyproject.toml`):
```toml
[tool.mypy]
python_version = "3.13"
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = true
```

### Pre-commit Hooks

```bash
# Install pre-commit
uv add --dev pre-commit

# Setup hooks
uv run pre-commit install

# Run manually
uv run pre-commit run --all-files
```

**Configuration** (`.pre-commit-config.yaml`):
```yaml
repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.6.0
    hooks:
      - id: ruff
        args: [--fix]
      - id: ruff-format
```

---

## Git Workflow

### Branch Strategy

```
main          # Production-ready code
  ↓
develop       # Integration branch
  ↓
feature/*     # New features
bugfix/*      # Bug fixes
hotfix/*      # Production hotfixes
```

### Commit Messages

Follow conventional commits:

```
<type>(<scope>): <subject>

<body>

<footer>
```

**Types**:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting, etc.)
- `refactor`: Code restructuring without behavior change
- `test`: Adding or updating tests
- `chore`: Maintenance tasks

**Examples**:
```
feat(auth): add password change endpoint

Implement POST /auth/change-password endpoint with token rotation.
Includes validation and error handling.

Closes #42
```

```
fix(user): prevent duplicate username registration

Add unique constraint check in UserService before creating user.

Fixes #38
```

### Pull Request Process

1. **Create feature branch**:
   ```bash
   git checkout -b feature/add-user-profile
   ```

2. **Make changes and commit**:
   ```bash
   git add .
   git commit -m "feat(user): add user profile endpoint"
   ```

3. **Push and create PR**:
   ```bash
   git push origin feature/add-user-profile
   ```

4. **PR checklist**:
   - [ ] Code follows style guidelines
   - [ ] Tests added/updated
   - [ ] Documentation updated
   - [ ] No linting errors
   - [ ] Commit messages follow conventions

---

## Database Migrations (Future)

When adding Alembic for migrations:

```bash
# Install Alembic
uv add alembic

# Initialize
uv run alembic init migrations

# Create migration
uv run alembic revision --autogenerate -m "add user profile table"

# Apply migration
uv run alembic upgrade head

# Rollback
uv run alembic downgrade -1
```

---

## Performance Guidelines

### Database Queries

**✅ Good Practices**:
- Use `select()` statements with filters
- Fetch only needed columns
- Use indexes for frequently queried columns
- Batch operations when possible

**❌ Avoid**:
- N+1 query problems
- Fetching all records without limit
- Unnecessary joins

### API Performance

- Return paginated results for large datasets
- Use background tasks for long-running operations
- Cache frequently accessed data (future: Redis)
- Use connection pooling for database

---

## Security Checklist

When adding new features:

- [ ] Input validation on all endpoints
- [ ] Authentication required for protected routes
- [ ] Sensitive data not in logs/responses
- [ ] SQL injection prevention (use parameterized queries)
- [ ] Rate limiting considered
- [ ] CORS properly configured
- [ ] No secrets in code (use environment variables)

---

## Documentation Requirements

When adding features, update:

1. **Code Comments**: For complex logic
2. **Docstrings**: For public functions/classes
3. **API Docs**: Update `docs/api-spec.md`
4. **Architecture**: Update `docs/architecture.md` if structure changes
5. **README**: Update if setup process changes

---

## Debugging Tips

### Enable Debug Logging

```python
# src/main.py
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

@app.middleware("http")
async def log_requests(request, call_next):
    logger.debug(f"Request: {request.method} {request.url}")
    response = await call_next(request)
    logger.debug(f"Response: {response.status_code}")
    return response
```

### VS Code Debugging

Use launch configuration from [setup.md](setup.md) and set breakpoints in code.

### Database Inspection

```bash
# Using SQLite CLI
sqlite3 dev.db

# Useful commands
.tables              # List all tables
.schema users        # Show table schema
SELECT * FROM users; # Query data
.quit                # Exit
```

---

## Common Patterns

### Dependency Injection

```python
from fastapi import Depends
from sqlmodel import Session
from src.config.database import get_session

@router.get("/users")
def list_users(
    session: Session = Depends(get_session),
    limit: int = 10,
    offset: int = 0
):
    # Use session
    pass
```

### Background Tasks

```python
from fastapi import BackgroundTasks

def send_email(email: str, message: str):
    # Long-running task
    pass

@router.post("/users")
def create_user(
    data: UserCreate,
    background_tasks: BackgroundTasks
):
    user = create_user_in_db(data)
    background_tasks.add_task(send_email, user.email, "Welcome!")
    return user
```

---

## Resources

- **FastAPI Docs**: https://fastapi.tiangolo.com/
- **SQLModel Docs**: https://sqlmodel.tiangolo.com/
- **Pydantic Docs**: https://docs.pydantic.dev/
- **Python Style Guide**: https://pep8.org/

---

## Getting Help

- Check existing documentation in `docs/`
- Review similar code in the codebase
- Ask questions in team chat/issues
- Consult FastAPI/SQLModel docs

---

*Last Updated: October 10, 2025*

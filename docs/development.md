# Development Guide

Guide for contributing to and developing the fs-backend project.

## Development Principles

### 1. Code Style & Standards

**Follow PEP 8** with these specifics:
- Line length: 88 characters (Black default)
- Use type hints for all function signatures
- Docstrings for public functions/classes (Google style)
- Prefer explicit over implicit

**Example**:
```python
from typing import Optional

def get_user_by_id(user_id: str, session: Session) -> Optional[User]:
    """
    Retrieve a user by their unique identifier.
    
    Args:
        user_id: UUID string of the user
        session: Database session
        
    Returns:
        User object if found, None otherwise
    """
    return session.query(User).filter(User.id == user_id).first()
```

### 2. Layer Responsibilities

**API Layer** (`src/api/`):
- Handle HTTP concerns only
- Validate request format (Pydantic handles this)
- Call service methods
- Return appropriate HTTP responses
- **Never** contain business logic

**Service Layer** (`src/services/`):
- Implement business logic
- Orchestrate multiple repository calls
- Enforce business rules
- Control transactions (commit/rollback)
- Raise domain exceptions

**Repository Layer** (`src/repositories/`):
- Database queries only
- Return entities or query results
- **Never** commit transactions
- **Never** contain business logic

### 3. Error Handling

**Use domain exceptions** (defined in `src/core/exceptions.py`):

```python
# ❌ Bad: Raising HTTPException in service
from fastapi import HTTPException

def create_user(username: str) -> User:
    if user_exists(username):
        raise HTTPException(status_code=409, detail="Username exists")

# ✅ Good: Raising domain exception
from src.core.exceptions import UserAlreadyExistsError

def create_user(username: str) -> User:
    if user_exists(username):
        raise UserAlreadyExistsError(f"Username '{username}' already exists")
```

Exception handlers in `main.py` map domain exceptions to HTTP responses.

### 4. Transaction Management

**Services control transactions**:

```python
# ✅ Good: Service commits
def create_user(data: UserCreate, session: Session) -> User:
    # Check business rules
    if self.user_repo.get_by_username(data.username, session):
        raise UserAlreadyExistsError()
    
    # Create entity
    user = User(
        username=data.username,
        hashed_password=hash_password(data.password)
    )
    
    # Repository adds to session
    self.user_repo.add(user, session)
    
    # Service commits
    session.commit()
    session.refresh(user)
    
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

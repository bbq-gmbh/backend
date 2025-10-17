# Testing Guide

Test suite for fs-backend with **fully isolated** in-memory SQLite database.

## Key Features

✅ **No .env file required** - Tests work without any environment configuration  
✅ **In-memory database** - Fresh `sqlite:///:memory:` database for each test  
✅ **Complete isolation** - Tests don't affect your development database  
✅ **Fast execution** - No disk I/O, pure memory operations  

## Structure

```
tests/
├── conftest.py          # Pytest config & shared fixtures
├── fixtures/            # Reusable fixtures
├── unit/                # Unit tests (services, logic)
└── integration/         # API endpoint tests
```

## Running Tests

```bash
# All tests
uv run pytest

# Specific file
uv run pytest tests/unit/test_services/test_user_service.py

# Specific test
uv run pytest tests/unit/test_services/test_user_service.py::TestUserCreation::test_create_user_success

# Stop on first failure
uv run pytest -x

# Verbose output
uv run pytest -v
```

## Key Fixtures

**From `conftest.py`:**
- `session` - In-memory database session
- `client` - FastAPI test client

**From `fixtures/user_fixtures.py`:**
- `created_user` - Pre-created test user
- `authenticated_client` - Client with auth token

## Writing Tests

**Unit test example:**
```python
def test_create_user(user_service, sample_user_data):
    user = user_service.create_user(sample_user_data)
    assert user.username == sample_user_data.username
```

**Integration test example:**
```python
def test_register(client):
    response = client.post(
        "/auth/register",
        json={"username": "newuser", "password": "password123"},
    )
    assert response.status_code == 200
```

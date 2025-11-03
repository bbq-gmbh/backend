"""User-related test fixtures."""

import pytest
from sqlmodel import Session

from app.models.user import User
from app.services.user import UserService
from app.services.auth import AuthService
from app.repositories.user import UserRepository
from app.repositories.employee import EmployeeRepository
from app.repositories.employee_hierarchy import EmployeeHierarchyRepository
from app.schemas.user import UserCreate


@pytest.fixture
def user_repository(session: Session):
    """Provide a user repository for tests."""
    return UserRepository(session=session)


@pytest.fixture
def employee_repository(session: Session):
    """Provide an employee repository for tests."""
    return EmployeeRepository(session=session)


@pytest.fixture
def employee_hierarchy_repository(session: Session):
    """Provide an employee hierarchy repository for tests."""
    return EmployeeHierarchyRepository(session=session)


@pytest.fixture
def user_service(user_repository: UserRepository, employee_repository: EmployeeRepository, employee_hierarchy_repository: EmployeeHierarchyRepository):
    """Provide a user service for tests."""
    return UserService(
        user_repo=user_repository,
        employee_repo=employee_repository,
        hierarchy_repo=employee_hierarchy_repository
    )


@pytest.fixture
def auth_service(user_repository: UserRepository):
    """Provide an auth service for tests."""
    return AuthService(user_repo=user_repository)


@pytest.fixture
def sample_user_data():
    """Provide sample user creation data."""
    return UserCreate(username="testuser", password="Test123!@#")


@pytest.fixture
def created_user(user_service: UserService, sample_user_data: UserCreate) -> User:
    """Create and return a test user."""
    return user_service.create_user(sample_user_data)


@pytest.fixture
def test_credentials():
    """Provide test user credentials."""
    return {"username": "testuser", "password": "Test123!@#"}


@pytest.fixture
def authenticated_client(client, created_user, test_credentials):
    """Provide a client with authenticated user and access token."""
    response = client.post("/auth/login", json=test_credentials)
    token_data = response.json()
    access_token = token_data["access_token"]

    client.headers = {"Authorization": f"Bearer {access_token}"}
    return client


@pytest.fixture
def superuser(session: Session) -> User:
    """Create and return a superuser for tests."""
    from app.core.security import hash_password

    superuser = User(
        username="superuser",
        password_hash=hash_password("SuperPass123!@#"),
        is_superuser=True,
    )
    session.add(superuser)
    session.commit()
    session.refresh(superuser)
    return superuser


@pytest.fixture
def superuser_client(client, superuser):
    """Provide a client with authenticated superuser and access token."""
    response = client.post(
        "/auth/login",
        json={"username": "superuser", "password": "SuperPass123!@#"},
    )
    token_data = response.json()
    access_token = token_data["access_token"]

    client.headers = {"Authorization": f"Bearer {access_token}"}
    return client

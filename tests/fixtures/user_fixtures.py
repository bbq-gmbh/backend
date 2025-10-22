"""User-related test fixtures."""

import pytest
from sqlmodel import Session

from app.models.user import User
from app.services.user import UserService
from app.repositories.user import UserRepository
from app.schemas.user import UserCreate


@pytest.fixture
def user_repository(session: Session):
    """Provide a user repository for tests."""
    return UserRepository(session=session)


@pytest.fixture
def user_service(user_repository: UserRepository):
    """Provide a user service for tests."""
    return UserService(user_repo=user_repository)


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

"""Pytest configuration and shared fixtures."""

import os
import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine
from sqlmodel.pool import StaticPool

# Set testing mode before importing app modules
os.environ["TESTING"] = "1"
os.environ["JWT_SECRET_KEY"] = "test-secret-key-for-testing-only"
os.environ["DATABASE_URL"] = "sqlite:///:memory:"

from app.config.database import get_session
from app.main import app


@pytest.fixture(name="session")
def session_fixture():
    """Create a fresh in-memory database for each test.
    
    Uses SQLite in-memory database which is completely isolated from
    the application's database and requires no .env file.
    Each test gets a fresh database with all tables created.
    """
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session


@pytest.fixture(name="client")
def client_fixture(session: Session):
    """Create a test client with database session override."""

    def get_session_override():
        return session

    app.dependency_overrides[get_session] = get_session_override
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()


# Import fixtures from fixtures directory
pytest_plugins = ["tests.fixtures.user_fixtures"]

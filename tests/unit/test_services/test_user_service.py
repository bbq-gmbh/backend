"""Unit tests for UserService."""

import uuid
import pytest

from app.core.exceptions import (
    UserAlreadyExistsError,
    UserNotFoundError,
    ValidationError,
)
from app.schemas.user import UserCreate


class TestUserCreation:
    """Test user creation functionality."""

    def test_create_user_success(self, user_service):
        """Test successful user creation."""
        user_data = UserCreate(username="newuser", password="NewPass123!@#")
        user = user_service.create_user(user_data)
        
        assert user.id is not None
        assert user.username == "newuser"
        assert user.password_hash is not None
        assert user.password_hash != "NewPass123!@#"

    def test_create_user_duplicate_username(self, user_service, created_user):
        """Test that creating duplicate username raises error."""
        duplicate_data = UserCreate(
            username=created_user.username, password="different123"
        )
        
        with pytest.raises(UserAlreadyExistsError) as exc_info:
            user_service.create_user(duplicate_data)
        
        assert created_user.username in str(exc_info.value)

    def test_create_user_short_username(self, user_service):
        """Test that short username raises validation error."""
        short_username = UserCreate(username="abc", password="validpass123")
        
        with pytest.raises(ValidationError) as exc_info:
            user_service.create_user(short_username)
        
        assert "at least 4 characters" in str(exc_info.value)

    def test_create_user_username_with_spaces(self, user_service):
        """Test that username with spaces raises validation error."""
        spaced_username = UserCreate(username="test user", password="validpass123")
        
        with pytest.raises(ValidationError) as exc_info:
            user_service.create_user(spaced_username)
        
        assert "cannot contain spaces" in str(exc_info.value)

    def test_create_user_short_password(self, user_service):
        """Test that short password raises validation error."""
        short_password = UserCreate(username="validuser", password="short")
        
        with pytest.raises(ValidationError) as exc_info:
            user_service.create_user(short_password)
        
        assert "at least 8 characters" in str(exc_info.value)


class TestUserRetrieval:
    """Test user retrieval functionality."""

    def test_get_user_by_id_success(self, user_service, created_user):
        """Test successful user retrieval by ID."""
        user = user_service.get_user_by_id(created_user.id)
        
        assert user is not None
        assert user.id == created_user.id
        assert user.username == created_user.username

    def test_get_user_by_id_not_found(self, user_service):
        """Test getting user with non-existent ID."""
        user = user_service.get_user_by_id(uuid.uuid4())
        
        assert user is None


class TestUserAuthentication:
    """Test user authentication functionality."""

    def test_authenticate_user_success(self, user_service, created_user):
        """Test successful user authentication."""
        user = user_service.authenticate_user("testuser", "Test123!@#")
        
        assert user is not None
        assert user.username == "testuser"

    def test_authenticate_user_invalid_password(self, user_service, created_user):
        """Test authentication with invalid password."""
        user = user_service.authenticate_user("testuser", "wrongpassword")
        
        assert user is None

    def test_authenticate_user_nonexistent(self, user_service):
        """Test authentication with nonexistent user."""
        user = user_service.authenticate_user("nonexistent", "Test123!@#")
        
        assert user is None


class TestUserListing:
    """Test user listing functionality."""

    def test_get_all_users(self, user_service, created_user):
        """Test listing all users."""
        users = user_service.get_all_users()
        
        assert len(users) >= 1
        assert any(u.username == "testuser" for u in users)

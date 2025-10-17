"""Unit tests for AuthService."""

import pytest
from app.core.exceptions import InvalidCredentialsError
from app.schemas.auth import TokenKind


class TestAuthentication:
    """Test authentication functionality."""

    def test_authenticate_user_success(
        self, user_service, created_user, test_credentials
    ):
        """Test successful user authentication."""
        from app.services.auth import AuthService

        auth_service = AuthService(user_service=user_service)

        user = user_service.authenticate_user(
            test_credentials["username"], test_credentials["password"]
        )

        assert user is not None
        assert user.id == created_user.id

    def test_authenticate_user_wrong_password(self, user_service, created_user):
        """Test authentication fails with wrong password."""
        user = user_service.authenticate_user(created_user.username, "wrongpassword")

        assert user is None


class TestTokenGeneration:
    """Test JWT token generation."""

    def test_issue_access_token(self, user_service, created_user):
        """Test access token generation."""
        from app.services.auth import AuthService

        auth_service = AuthService(user_service=user_service)

        token = auth_service.issue_access_token(created_user)

        assert isinstance(token, str)
        assert len(token) > 0

    def test_issue_token_pair(self, user_service, created_user):
        """Test token pair generation."""
        from app.services.auth import AuthService

        auth_service = AuthService(user_service=user_service)

        access_token, refresh_token = auth_service.issue_token_pair(created_user)

        assert isinstance(access_token, str)
        assert len(access_token) > 0
        assert isinstance(refresh_token, str)
        assert len(refresh_token) > 0


class TestTokenDecoding:
    """Test JWT token decoding."""

    def test_decode_token_valid(self, user_service, created_user):
        """Test decoding a valid access token."""
        from app.services.auth import AuthService

        auth_service = AuthService(user_service=user_service)

        token = auth_service.issue_access_token(created_user)
        token_data = auth_service.decode_token(token)

        assert token_data is not None
        assert token_data.sub == created_user.id
        assert token_data.kind == TokenKind.ACCESS

    def test_decode_token_invalid(self, user_service):
        """Test decoding an invalid token."""
        from app.services.auth import AuthService

        auth_service = AuthService(user_service=user_service)

        token_data = auth_service.decode_token("invalid.token.here")

        assert token_data is None

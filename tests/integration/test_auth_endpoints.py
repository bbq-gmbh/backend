"""Integration tests for authentication endpoints."""

import pytest
from fastapi.testclient import TestClient


class TestLogin:
    """Test login endpoint."""

    def test_login_success(self, client, created_user, test_credentials):
        """Test successful login with valid credentials."""
        response = client.post(
            "/auth/login",
            json={
                "username": test_credentials["username"],
                "password": test_credentials["password"],
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"

    def test_login_invalid_username(self, client):
        """Test login with nonexistent username."""
        response = client.post(
            "/auth/login",
            json={"username": "nonexistent", "password": "Test123!@#"},
        )

        assert response.status_code == 401

    def test_login_invalid_password(self, client, created_user):
        """Test login with incorrect password."""
        response = client.post(
            "/auth/login",
            json={"username": "testuser", "password": "wrongpassword"},
        )

        assert response.status_code == 401

    def test_login_missing_credentials(self, client):
        """Test login without credentials."""
        response = client.post("/auth/login", json={})

        assert response.status_code == 422  # Validation error


class TestRefreshToken:
    """Test refresh token endpoint."""

    def test_refresh_token_success(self, client, created_user):
        """Test refreshing access token with valid refresh token."""
        # First, login to get both tokens
        login_response = client.post(
            "/auth/login",
            json={"username": "testuser", "password": "Test123!@#"}
        )
        refresh_token = login_response.json()["refresh_token"]

        # Use refresh token to get new access token
        response = client.post(
            "/auth/refresh",
            headers={"Authorization": f"Bearer {refresh_token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert "token" in data
        assert "token_type" in data
        assert data["token_type"] == "bearer"

    def test_refresh_token_without_auth(self, client):
        """Test refresh without authorization header."""
        response = client.post("/auth/refresh")

        assert response.status_code == 403  # HTTPBearer returns 403 for missing auth

    def test_refresh_token_invalid(self, client):
        """Test refresh with invalid token."""
        response = client.post(
            "/auth/refresh",
            headers={"Authorization": "Bearer invalid.token.here"},
        )

        assert response.status_code == 401


class TestChangePassword:
    """Test password change endpoint."""

    def test_change_password_success(self, authenticated_client):
        """Test successful password change."""
        response = authenticated_client.post(
            "/auth/change-password",
            json={
                "current_password": "Test123!@#",
                "new_password": "NewPass456!@#",
            },
        )

        assert response.status_code == 204  # No content on success

    def test_change_password_wrong_current(self, authenticated_client):
        """Test password change with wrong current password."""
        response = authenticated_client.post(
            "/auth/change-password",
            json={
                "current_password": "WrongPassword",
                "new_password": "NewPass456!@#",
            },
        )

        assert response.status_code == 401

    def test_change_password_too_short(self, authenticated_client):
        """Test password change with too short new password."""
        response = authenticated_client.post(
            "/auth/change-password",
            json={
                "current_password": "Test123!@#",
                "new_password": "short",
            },
        )

        assert response.status_code == 422

    def test_change_password_unauthenticated(self, client):
        """Test password change without authentication."""
        response = client.post(
            "/auth/change-password",
            json={
                "current_password": "Test123!@#",
                "new_password": "NewPass456!@#",
            },
        )

        assert response.status_code == 403  # HTTPBearer returns 403 for missing auth


class TestLogout:
    """Test logout endpoint."""

    def test_logout_success(self, authenticated_client):
        """Test successful logout."""
        response = authenticated_client.post("/auth/logout-all")

        assert response.status_code == 204  # No content on success

    def test_logout_unauthenticated(self, client):
        """Test logout without authentication."""
        response = client.post("/auth/logout-all")

        assert response.status_code == 403  # HTTPBearer returns 403 for missing auth

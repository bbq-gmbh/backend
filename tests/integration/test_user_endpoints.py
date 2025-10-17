"""Integration tests for user endpoints."""

import pytest


class TestCreateUser:
    """Test POST /users endpoint."""

    def test_create_user_success(self, client):
        """Test successful user creation via API."""
        response = client.post(
            "/users",
            json={"username": "apiuser", "password": "password123"},
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["username"] == "apiuser"
        assert "id" in data
        assert "password" not in data
        assert "hashed_password" not in data

    def test_create_user_duplicate(self, client, created_user):
        """Test creating user with duplicate username."""
        response = client.post(
            "/users",
            json={"username": created_user.username, "password": "password123"},
        )
        
        assert response.status_code == 409


class TestListUsers:
    """Test GET /users endpoint."""

    def test_list_users_requires_auth(self, client):
        """Test that listing users requires authentication."""
        response = client.get("/users")
        assert response.status_code == 403  # HTTPBearer returns 403 when no auth provided

    def test_list_users_success(self, client, authenticated_client):
        """Test successful user listing."""
        response = authenticated_client.get("/users")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1
        
        # Verify user data structure
        user_data = data[0]
        assert "id" in user_data
        assert "username" in user_data
        assert "password" not in user_data
        assert "hashed_password" not in user_data

    def test_list_users_invalid_token(self, client):
        """Test listing users with invalid token."""
        response = client.get(
            "/users",
            headers={"Authorization": "Bearer invalid.token.here"},
        )
        
        assert response.status_code == 401

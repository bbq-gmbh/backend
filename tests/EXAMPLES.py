"""Quick test examples for common scenarios."""

# 1. Test a service method
def test_user_creation(user_service):
    from app.schemas.user import UserCreate
    
    user_data = UserCreate(username="testuser", password="password123")
    user = user_service.create_user(user_data)
    
    assert user.username == "testuser"


# 2. Test an API endpoint
def test_register_endpoint(client):
    response = client.post(
        "/auth/register",
        json={"username": "newuser", "password": "password123"},
    )
    
    assert response.status_code == 200
    assert "access_token" in response.json()


# 3. Test authenticated endpoint
def test_protected_endpoint(authenticated_client):
    auth_client, user, tokens = authenticated_client
    
    response = auth_client.get("/users")
    
    assert response.status_code == 200


# 4. Test exception handling
def test_validation_error(user_service):
    import pytest
    from app.core.exceptions import ValidationError
    from app.schemas.user import UserCreate
    
    short_username = UserCreate(username="abc", password="password123")
    
    with pytest.raises(ValidationError) as exc_info:
        user_service.create_user(short_username)
    
    assert "at least 4 characters" in str(exc_info.value)


# 5. Test with parametrize
import pytest

@pytest.mark.parametrize("username,password,expected_error", [
    ("abc", "password123", "at least 4 characters"),
    ("test user", "password123", "cannot contain spaces"),
    ("validuser", "short", "at least 8 characters"),
])
def test_user_validation(user_service, username, password, expected_error):
    from app.core.exceptions import ValidationError
    from app.schemas.user import UserCreate
    
    user_data = UserCreate(username=username, password=password)
    
    with pytest.raises(ValidationError) as exc_info:
        user_service.create_user(user_data)
    
    assert expected_error in str(exc_info.value)

from fastapi import APIRouter, status

from app.api.dependencies import (
    AuthServiceDep,
    CurrentUserDep,
    UserFromRefreshTokenDep,
    UserServiceDep,
)
from app.schemas.auth import LoginRequest, TokenPair
from app.core.exceptions import InvalidCredentialsError
from app.schemas.user import UserCreate
from app.schemas.user import PasswordChangeRequest

router = APIRouter()


@router.post(
    "/register",
    name="Register User",
    operation_id="registerUser",
    response_model=TokenPair,
)
def register(
    user_in: UserCreate,
    user_service: UserServiceDep,
    auth_service: AuthServiceDep,
) -> TokenPair:
    user = user_service.create_user(user_in)
    access_token, refresh_token = auth_service.issue_token_pair(user)
    return TokenPair(access_token=access_token, refresh_token=refresh_token)


@router.post(
    "/login",
    name="Login User",
    operation_id="loginUser",
    response_model=TokenPair,
)
def login(
    login_data: LoginRequest,
    user_service: UserServiceDep,
    auth_service: AuthServiceDep,
) -> TokenPair:
    user = user_service.authenticate_user(
        username=login_data.username, password=login_data.password
    )
    if not user:
        raise InvalidCredentialsError()
    access_token, refresh_token = auth_service.issue_token_pair(user)
    return TokenPair(access_token=access_token, refresh_token=refresh_token)


@router.post(
    "/logout-all",
    name="Logout All Sessions",
    operation_id="logoutAllSessions",
    status_code=status.HTTP_204_NO_CONTENT,
)
def logout_all(current_user: CurrentUserDep, user_service: UserServiceDep) -> None:
    """Logs out from all devices by rotating the token key (invalidates all tokens)."""
    user_service.rotate_token_key(current_user)


@router.post(
    "/refresh",
    name="Refresh Tokens",
    operation_id="refreshTokens",
    response_model=TokenPair,
)
def refresh_token(user: UserFromRefreshTokenDep, auth_service: AuthServiceDep) -> TokenPair:
    """Refreshes both access and refresh tokens using a valid refresh token."""
    access_token, refresh_token = auth_service.issue_token_pair(user)
    return TokenPair(access_token=access_token, refresh_token=refresh_token)


@router.post(
    "/change-password",
    name="Change Password",
    operation_id="changePassword",
    status_code=status.HTTP_204_NO_CONTENT,
)
def change_password(
    payload: PasswordChangeRequest,
    current_user: CurrentUserDep,
    user_service: UserServiceDep,
) -> None:
    """Changes the current user's password and invalidates existing tokens."""
    user_service.change_password(
        user=current_user,
        current_password=payload.current_password,
        new_password=payload.new_password,
    )

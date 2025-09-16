from fastapi import APIRouter, status

from src.api.dependencies import (
    AuthServiceDep,
    CurrentUserDep,
    UserFromRefreshTokenDep,
    UserServiceDep,
)
from src.schemas.auth import LoginRequest, Token, TokenPair
from src.core.exceptions import InvalidCredentialsError
from src.schemas.user import UserCreate
from src.schemas.user import PasswordChangeRequest

router = APIRouter()


@router.post("/register", response_model=TokenPair)
def register(
    user_in: UserCreate,
    user_service: UserServiceDep,
    auth_service: AuthServiceDep,
) -> TokenPair:
    user = user_service.create_user(user_in)
    access_token, refresh_token = auth_service.issue_token_pair(user)
    return TokenPair(access_token=access_token, refresh_token=refresh_token)


@router.post("/login", response_model=TokenPair)
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


@router.post("/logout-all", status_code=status.HTTP_204_NO_CONTENT)
def logout_all(current_user: CurrentUserDep, user_service: UserServiceDep) -> None:
    """Logs out from all devices by rotating the token key (invalidates all tokens)."""
    user_service.rotate_token_key(current_user)


@router.post("/refresh", response_model=Token)
def refresh_token(user: UserFromRefreshTokenDep, auth_service: AuthServiceDep) -> Token:
    """Refreshes an access token using a valid refresh token."""
    new_access_token = auth_service.issue_access_token(user)
    return Token(token=new_access_token)


@router.post("/change-password", status_code=status.HTTP_204_NO_CONTENT)
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

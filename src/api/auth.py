from fastapi import APIRouter, HTTPException, status

from src.api.dependencies import (
    AuthServiceDep,
    CurrentUserDep,
    UserServiceDep,
)
from src.schemas.auth import AccessToken, LoginRequest, RefreshTokenRequest, Token
from src.schemas.user import UserCreate

router = APIRouter()


@router.post("/register", response_model=Token)
def register(
    user_in: UserCreate, user_service: UserServiceDep, auth_service: AuthServiceDep
):
    user = user_service.create_user(user_in)
    access_token, refresh_token = auth_service.create_token_pair(user)
    return Token(access_token=access_token, refresh_token=refresh_token)


@router.post("/login", response_model=Token)
def login(
    login_data: LoginRequest,
    user_service: UserServiceDep,
    auth_service: AuthServiceDep,
):
    user = user_service.authenticate_user(
        username=login_data.username, password=login_data.password
    )
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token, refresh_token = auth_service.create_token_pair(user)
    return Token(access_token=access_token, refresh_token=refresh_token)


@router.post("/logout-all", status_code=status.HTTP_204_NO_CONTENT)
def logout_all(current_user: CurrentUserDep, user_service: UserServiceDep):
    """Logs out from all devices by invalidating all tokens."""
    user_service.invalidate_all_tokens(current_user)


@router.post("/refresh", response_model=AccessToken)
def refresh_token(refresh_request: RefreshTokenRequest, auth_service: AuthServiceDep):
    """Refreshes an access token using a valid refresh token."""
    new_access_token = auth_service.refresh_access_token(refresh_request.refresh_token)
    if not new_access_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return AccessToken(access_token=new_access_token)

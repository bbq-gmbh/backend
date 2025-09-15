from fastapi import APIRouter, HTTPException, status

from src.api.dependencies import (
    AuthenticatedUserDep,
    AuthServiceDep,
    UserServiceDep,
)
from src.schemas.auth import LoginRequest, Token
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
def logout_all(current_user: CurrentUser, user_service: UserServiceDep):
    """Logs out from all devices by invalidating all tokens."""
    user_service.invalidate_all_tokens(current_user)

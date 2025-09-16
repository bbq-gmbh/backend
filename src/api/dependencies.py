from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlmodel import Session

from src.config.database import get_session
from src.models.user import User
from src.repositories.user import UserRepository
from src.schemas.auth import TokenData
from src.services.auth import AuthService
from src.services.user import UserService

bearer_scheme = HTTPBearer()

DatabaseSession = Annotated[Session, Depends(get_session)]


def get_user_repository(session: DatabaseSession) -> UserRepository:
    """Provides a user repository dependency."""
    return UserRepository(session=session)


UserRepositoryDep = Annotated[UserRepository, Depends(get_user_repository)]


def get_user_service(
    user_repo: UserRepositoryDep,
) -> UserService:
    """Provides a user service dependency."""
    return UserService(user_repository=user_repo)


UserServiceDep = Annotated[UserService, Depends(get_user_service)]


def get_auth_service(user_service: UserServiceDep) -> AuthService:
    """Provides an auth service dependency."""
    return AuthService(user_service=user_service)


AuthServiceDep = Annotated[AuthService, Depends(get_auth_service)]


def get_token_data(
    token: Annotated[HTTPAuthorizationCredentials, Depends(bearer_scheme)],
    auth_service: AuthServiceDep,
) -> TokenData:
    """
    Decodes the bearer token and retrieves the token data.

    Raises HTTPException for invalid credentials.

    Returns the TokenData schema.
    """
    data = auth_service.get_token_data(token.credentials)
    if not data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return data


TokenDataDep = Annotated[TokenData, Depends(get_token_data)]


def get_access_token_data(
    token_data: TokenDataDep,
) -> TokenData:
    """
    Returns token data if it's an access token.
    """
    if token_data.kind != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type, expected access token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return token_data


AccessTokenDataDep = Annotated[TokenData, Depends(get_access_token_data)]


def get_refresh_token_data(
    token_data: TokenDataDep,
) -> TokenData:
    """
    Returns token data if it's a refresh token.
    """
    if token_data.kind != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type, expected refresh token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return token_data


RefreshTokenDataDep = Annotated[TokenData, Depends(get_refresh_token_data)]


def get_current_user(
    token_data: AccessTokenDataDep,
    user_service: UserServiceDep,
) -> User:
    """
    Retrieves the user from the database from an access token.

    Raises HTTPException for user not found.

    Returns the authenticated User model.
    """
    user = user_service.get_user_by_id(token_data.sub)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


CurrentUserDep = Annotated[User, Depends(get_current_user)]


def get_user_from_refresh_token(
    token_data: RefreshTokenDataDep,
    user_service: UserServiceDep,
) -> User:
    """
    Retrieves the user from the database from a refresh token.

    Raises HTTPException for user not found.

    Returns the authenticated User model.
    """
    user = user_service.get_user_by_id(token_data.sub)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


UserFromRefreshTokenDep = Annotated[User, Depends(get_user_from_refresh_token)]

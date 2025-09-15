from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlmodel import Session

from src.config.database import get_session
from src.models.user import User
from src.repositories.user import UserRepository
from src.services.auth import AuthService
from src.services.user import UserService


# Annotated dependencies for direct use
DatabaseSession = Annotated[Session, Depends(get_session)]

bearer_scheme = HTTPBearer()


# Provider functions using Annotated
def get_user_repository(session: DatabaseSession) -> UserRepository:
    """Provides a user repository dependency."""
    return UserRepository(session=session)


UserRepositoryDep = Annotated[UserRepository, Depends(get_user_repository)]


def get_user_service(
    user_repo: UserRepositoryDep,
) -> UserService:
    """Provides a user service dependency."""
    return UserService(user_repository=user_repo)


# Final dependency for path operation functions
UserServiceDep = Annotated[UserService, Depends(get_user_service)]


def get_auth_service(user_service: UserServiceDep) -> AuthService:
    """Provides an auth service dependency."""
    return AuthService(user_service=user_service)


AuthServiceDep = Annotated[AuthService, Depends(get_auth_service)]


def get_current_user(
    token: Annotated[HTTPAuthorizationCredentials, Depends(bearer_scheme)],
    auth_service: AuthServiceDep,
) -> User:
    """
    Decodes the bearer token, retrieves the user from the database,
    and validates the token's validation key against the user's.

    Raises HTTPException for invalid credentials, user not found, or
    mismatched validation key.

    Returns the authenticated User model.
    """
    user = auth_service.get_user_from_token(token.credentials)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]

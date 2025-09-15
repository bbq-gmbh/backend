from typing import Annotated

from fastapi import Depends
from sqlmodel import Session

from src.config.database import get_session
from src.repositories.user import UserRepository
from src.services.user import UserService


def get_user_repository(session: Session = Depends(get_session)) -> UserRepository:
    return UserRepository(session)


def get_user_service(
    user_repo: UserRepository = Depends(get_user_repository),
) -> UserService:
    return UserService(user_repo)


DBSession = Annotated[Session, Depends(get_session)]
CurrentUserRepository = Annotated[UserRepository, Depends(get_user_repository)]
CurrentUserService = Annotated[UserService, Depends(get_user_service)]

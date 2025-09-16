from typing import Optional

from src.core.security import verify_password
from src.models.user import User
import logging
from sqlmodel import Session

from src.repositories.user import UserRepository
from src.core.exceptions import UserAlreadyExistsError
from src.schemas.user import UserCreate


class UserService:
    def __init__(self, user_repository: UserRepository):
        self.user_repository = user_repository
        self._session: Session = user_repository.session
        self._log = logging.getLogger("app.user_service")

    def create_user(self, user_in: UserCreate) -> User:
        username = user_in.username

        # Validate username basics (push richer rules to Pydantic later if needed)
        if not username:
            raise ValueError("Username cannot be empty")
        if len(username) < 4:
            raise ValueError("Username must be at least 4 characters")
        if " " in username:
            raise ValueError("Username cannot contain spaces")

        # Uniqueness
        if self.user_repository.get_user_by_username(username):
            self._log.info("user.create.duplicate username=%s", username)
            raise UserAlreadyExistsError(username)

        # Persist
        user = self.user_repository.create_user(user_in)
        self._session.commit()
        self._session.refresh(user)
        self._log.info("user.create.success id=%s username=%s", user.id, username)
        return user

    def get_user_by_id(self, user_id: str) -> Optional[User]:
        return self.user_repository.get_user_by_id(user_id)

    def authenticate_user(self, username: str, password: str) -> Optional[User]:
        user = self.user_repository.get_user_by_username(username)
        if not user:
            return None
        if not verify_password(password, user.password_hash):
            return None
        return user

    def rotate_token_key(self, user: User):
        self.user_repository.rotate_token_key(user)
        self._session.commit()
        self._session.refresh(user)
        self._log.info("user.token.rotate id=%s new_key=%s", user.id, user.token_key)

    def get_all_users(self) -> list[User]:
        """Retrieves all users."""
        return self.user_repository.get_all_users()

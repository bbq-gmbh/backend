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
        # Basic validation (defer to Pydantic enhancements later if needed)
        username = user_in.username.strip()
        if len(username) < 3:
            raise ValueError("Username too short")
        # Uniqueness check
        existing = self.user_repository.get_user_by_username(username)
        if existing:
            self._log.info("user.create.duplicate username=%s", username)
            raise UserAlreadyExistsError(username)
        user_in.username = username  # mutate for repository usage
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

    def rotate_token_version(self, user: User):
        self.user_repository.update_token_version(user)
        self._session.commit()
        self._session.refresh(user)
        self._log.info(
            "user.token.rotate id=%s new_version=%s", user.id, user.token_version
        )

    def get_all_users(self) -> list[User]:
        """Retrieves all users."""
        return self.user_repository.get_all_users()

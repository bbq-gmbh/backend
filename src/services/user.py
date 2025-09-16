from typing import Optional

from src.core.security import verify_password
from src.models.user import User
import logging
from sqlmodel import Session

from src.repositories.user import UserRepository
from src.core.exceptions import (
    UserAlreadyExistsError,
    ValidationError,
    InvalidCredentialsError,
)
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
            raise ValidationError("Username cannot be empty")
        if len(username) < 4:
            raise ValidationError("Username must be at least 4 characters")
        if " " in username:
            raise ValidationError("Username cannot contain spaces")

        # Basic password validation (kept intentionally minimal; adjust as needed)
        password = user_in.password
        if not password:
            raise ValidationError("Password cannot be empty")
        if len(password) < 8:
            raise ValidationError("Password must be at least 8 characters")

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

    def change_password(self, user: User, current_password: str, new_password: str):
        # Verify current password
        if not verify_password(current_password, user.password_hash):
            raise InvalidCredentialsError()
        # Basic new password validation (align with create_user rules)
        if not new_password:
            raise ValidationError("New password cannot be empty")
        if len(new_password) < 8:
            raise ValidationError("New password must be at least 8 characters")
        if current_password == new_password:
            raise ValidationError("New password must differ from current password")
        # Persist hash & rotate token key to invalidate existing tokens
        self.user_repository.update_password(user, new_password)
        self.user_repository.rotate_token_key(user)
        self._session.commit()
        self._session.refresh(user)
        self._log.info("user.password.changed id=%s", user.id)

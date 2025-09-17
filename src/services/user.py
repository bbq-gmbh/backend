import uuid
import logging

from typing import Optional

from src.core.security import verify_password
from src.models.user import User
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

    def _validate_username(self, username: str):
        """Validates username rules.

        Keep this in sync with any API documentation or client-side validation.
        """
        if not username:
            raise ValidationError("Username cannot be empty")
        if len(username) < 4:
            raise ValidationError("Username must be at least 4 characters")
        if " " in username:
            raise ValidationError("Username cannot contain spaces")

    def _validate_password(self, password: str):
        """Validates password creation/update rules (length, non-empty).

        NOTE: Keep in sync with any future policy (complexity, entropy, blacklist, etc.).
        """
        if not password:
            raise ValidationError("Password cannot be empty")
        if len(password) < 8:
            raise ValidationError("Password must be at least 8 characters")

    def create_user(self, user_in: UserCreate) -> User:
        username = user_in.username

        self._validate_username(username)
        self._validate_password(user_in.password)
        if self.user_repository.get_user_by_username(username):
            self._log.info("user.create.duplicate username=%s", username)
            raise UserAlreadyExistsError(username)
        user = self.user_repository.create_user(user_in)
        self._session.commit()
        self._session.refresh(user)
        self._log.info("user.create.success id=%s username=%s", user.id, username)
        return user

    def get_user_by_id(self, user_id: uuid.UUID) -> Optional[User]:
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
        if not verify_password(current_password, user.password_hash):
            raise InvalidCredentialsError()

        self._validate_password(new_password)
        if current_password == new_password:
            raise ValidationError("New password must differ from current password")

        self.user_repository.update_password(user, new_password)
        self.user_repository.rotate_token_key(user)
        self._session.commit()
        self._session.refresh(user)
        self._log.info("user.password.changed id=%s", user.id)

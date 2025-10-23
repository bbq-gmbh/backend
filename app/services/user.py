from typing import Optional

from app.core.security import verify_password
from app.models.user import User

from app.repositories.user import UserRepository
from app.core.exceptions import (
    UserAlreadyExistsError,
    ValidationError,
    InvalidCredentialsError,
)
from app.schemas.user import UserCreate


class UserService:
    def __init__(self, user_repo: UserRepository):
        self.user_repo = user_repo
        self.session = user_repo.session

    @staticmethod
    def _validate_username(username: str):
        """Validates username rules.

        Keep this in sync with any API documentation or client-side validation.
        """
        if not username:
            raise ValidationError("Username cannot be empty")
        if len(username) < 4:
            raise ValidationError("Username must be at least 4 characters")
        if " " in username:
            raise ValidationError("Username cannot contain spaces")

    @staticmethod
    def _validate_password(password: str):
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

        if self.user_repo.get_user_by_username(username):
            raise UserAlreadyExistsError(username)

        user = self.user_repo.create_user(user_in)
        self.session.commit()
        self.session.refresh(user)

        return user

    def authenticate_user(self, username: str, password: str) -> Optional[User]:
        user = self.user_repo.get_user_by_username(username)
        if not user:
            return None

        if not verify_password(password, user.password_hash):
            return None

        return user

    def rotate_token_key(self, user: User):
        self.user_repo.rotate_token_key(user)
        self.session.commit()
        self.session.refresh(user)

    def get_all_users(self) -> list[User]:
        """Retrieves all users."""
        return self.user_repo.get_all_users()

    def change_password(self, user: User, current_password: str, new_password: str):
        if not verify_password(current_password, user.password_hash):
            raise InvalidCredentialsError()

        self._validate_password(new_password)
        if current_password == new_password:
            raise ValidationError("New password must differ from current password")

        self.user_repo.update_password(user, new_password)
        self.user_repo.rotate_token_key(user)
        self.session.commit()
        self.session.refresh(user)

from typing import Optional

from src.core.security import verify_password
from src.models.user import User
from src.repositories.user import UserRepository
from src.schemas.user import CreateUserRequest


class UserService:
    def __init__(self, user_repository: UserRepository):
        self.user_repository = user_repository

    def create_user(self, user_in: CreateUserRequest) -> User:
        return self.user_repository.create_user(user_in)

    def get_user_by_id(self, user_id: str) -> Optional[User]:
        return self.user_repository.get_user_by_id(user_id)

    def authenticate_user(self, username: str, password: str) -> Optional[User]:
        user = self.user_repository.get_user_by_username(username)
        if not user:
            return None
        if not verify_password(password, user.password_hash):
            return None
        return user

    def invalidate_all_tokens(self, user: User):
        self.user_repository.update_validation_key(user)

    def get_all_users(self) -> list[User]:
        """Retrieves all users."""
        return self.user_repository.get_all_users()

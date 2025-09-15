from src.models.user import User
from src.repositories.user import UserRepository
from src.schemas.user import UserCreate


class UserService:
    def __init__(self, user_repository: UserRepository):
        self.user_repository = user_repository

    def create_user(self, user_in: UserCreate) -> User:
        return self.user_repository.create_user(user_in)

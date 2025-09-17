import uuid
from typing import Optional

from sqlmodel import Session, select

from src.core.security import hash_password
from src.models.user import User
from src.schemas.user import UserCreate


class UserRepository:
    def __init__(self, session: Session):
        self.session = session

    def create_user(self, user_in: UserCreate) -> User:
        user = User(
            username=user_in.username, password_hash=hash_password(user_in.password)
        )
        self.session.add(user)
        return user

    def get_user_by_id(self, user_id: uuid.UUID) -> Optional[User]:
        return self.session.get(User, user_id)

    def get_user_by_username(self, username: str) -> Optional[User]:
        statement = select(User).where(User.username == username)
        return self.session.exec(statement).first()

    def rotate_token_key(self, user: User):
        user.token_key = uuid.uuid4()
        self.session.add(user)

    def update_password(self, user: User, new_password: str):
        user.password_hash = hash_password(new_password)
        self.session.add(user)

    def get_all_users(self) -> list[User]:
        """Retrieves all users from the database."""
        return list(self.session.exec(select(User)).all())

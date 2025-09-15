from sqlmodel import Session

from src.core.security import get_password_hash
from src.models.user import User
from src.schemas.user import UserCreate


class UserRepository:
    def __init__(self, session: Session):
        self.session = session

    def create_user(self, user_in: UserCreate) -> User:
        user = User(
            username=user_in.username, password_hash=get_password_hash(user_in.password)
        )
        self.session.add(user)
        self.session.commit()
        self.session.refresh(user)
        return user

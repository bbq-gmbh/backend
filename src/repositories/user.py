import uuid

from sqlmodel import Session, select

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

    def get_user_by_id(self, user_id: str) -> User | None:
        return self.session.get(User, user_id)

    def get_user_by_username(self, username: str) -> User | None:
        statement = select(User).where(User.username == username)
        return self.session.exec(statement).first()

    def update_validation_key(self, user: User):
        user.validation_key = str(uuid.uuid4())
        self.session.add(user)
        self.session.commit()
        self.session.refresh(user)

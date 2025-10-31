import uuid
from typing import Optional

from sqlmodel import Session, func, select

from app.core.security import hash_password
from app.models.employee import Employee
from app.models.employee_hierarchy import EmployeeHierarchy
from app.models.user import User
from app.schemas.user import UserCreate


class UserRepository:
    def __init__(self, session: Session):
        self.session = session

    def create_user(self, user_in: UserCreate) -> User:
        user = User(
            username=user_in.username, password_hash=hash_password(user_in.password)
        )
        self.session.add(user)
        return user

    def delete_user(self, target: User):
        self.session.delete(target)

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

    def get_users(self, page: int, page_size: int) -> list[User]:
        exec = select(User).limit(page_size).offset(page * page_size)
        return list(self.session.exec(exec).all())

    def get_users_count(self) -> int:
        return self.session.scalar(select(func.count()).select_from(User)) or 0

    def get_user_employee_pairs(
        self, page: int, page_size: int
    ) -> list[tuple[User, Optional[Employee]]]:
        exec = (
            select(User, Employee)
            .join(Employee, isouter=True)
            .limit(page_size)
            .offset(page * page_size)
        )
        return list(self.session.exec(exec).all())

    def get_user_employee_pairs_count(self) -> int:
        return (
            self.session.scalar(
                select(func.count()).select_from(
                    select(User, Employee).join(Employee, isouter=True).subquery()
                )
            )
            or 0
        )

    def get_lower_user_employee_pairs_paged(
        self, target: Employee, page: int, page_size: int, *, same: bool = False
    ) -> list[tuple[User, Employee]]:
        exec = (
            select(User, Employee)
            .join(Employee)
            .join(
                EmployeeHierarchy,
                Employee.user_id == EmployeeHierarchy.descendant_id,  # type: ignore
            )
            .where(EmployeeHierarchy.ancestor_id == target.user_id)
            .where(EmployeeHierarchy.depth >= int(not same))
            .limit(page_size)
            .offset(page * page_size)
        )

        result = self.session.exec(exec)
        return list(result.all())

    def get_lower_user_employee_pairs_paged_count(
        self, target: Employee, *, same: bool = False
    ) -> int:
        exec = (
            select(User, Employee)
            .join(Employee)
            .join(
                EmployeeHierarchy,
                Employee.user_id == EmployeeHierarchy.descendant_id,  # type: ignore
            )
            .where(EmployeeHierarchy.ancestor_id == target.user_id)
            .where(EmployeeHierarchy.depth >= int(not same))
        )

        return (
            self.session.scalar(select(func.count()).select_from(exec.subquery())) or 0
        )

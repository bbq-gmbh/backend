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

    def get_users_filtered(
        self, page: int, page_size: int, is_employee: Optional[bool] = None
    ) -> list[User]:
        """Get users with optional employee status filter."""
        query = select(User)

        if is_employee is not None:
            if is_employee:
                query = query.where(User.employee.is_not(None))  # type: ignore
            else:
                query = query.where(User.employee.is_(None))  # type: ignore

        query = query.limit(page_size).offset(page * page_size)
        return list(self.session.exec(query).all())

    def get_users_filtered_count(self, is_employee: Optional[bool] = None) -> int:
        """Count users with optional employee status filter."""
        query = select(func.count()).select_from(User)

        if is_employee is not None:
            if is_employee:
                query = query.where(User.employee.is_not(None))  # type: ignore
            else:
                query = query.where(User.employee.is_(None))  # type: ignore

        return self.session.scalar(query) or 0

    def search_users_by_username(
        self, username_query: str, page: int, page_size: int
    ) -> list[User]:
        """Search users by username using case-insensitive substring matching."""
        statement = (
            select(User)
            .where(User.username.ilike(f"%{username_query}%"))  # type: ignore
            .limit(page_size)
            .offset(page * page_size)
        )
        return list(self.session.exec(statement).all())

    def search_users_by_username_count(self, username_query: str) -> int:
        """Count users matching the username search query."""
        statement = (
            select(func.count())
            .select_from(User)
            .where(User.username.ilike(f"%{username_query}%"))  # type: ignore
        )
        return self.session.scalar(statement) or 0

    def search_users_by_username_filtered(
        self,
        username_query: str,
        page: int,
        page_size: int,
        is_employee: Optional[bool] = None,
    ) -> list[User]:
        """Search users by username with optional employee status filter."""
        query = select(User).where(User.username.ilike(f"%{username_query}%"))  # type: ignore

        if is_employee is not None:
            if is_employee:
                query = query.where(User.employee.is_not(None))  # type: ignore
            else:
                query = query.where(User.employee.is_(None))  # type: ignore

        query = query.limit(page_size).offset(page * page_size)
        return list(self.session.exec(query).all())

    def search_users_by_username_filtered_count(
        self, username_query: str, is_employee: Optional[bool] = None
    ) -> int:
        """Count users matching search query with optional employee status filter."""
        query = (
            select(func.count())
            .select_from(User)
            .where(User.username.ilike(f"%{username_query}%"))  # type: ignore
        )  # type: ignore

        if is_employee is not None:
            if is_employee:
                query = query.where(User.employee.is_not(None))  # type: ignore
            else:
                query = query.where(User.employee.is_(None))  # type: ignore

        return self.session.scalar(query) or 0

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

    def is_employee_lower(
        self, target_id: uuid.UUID, other_id: uuid.UUID, *, same: bool = False
    ) -> bool:
        exec = (
            select(EmployeeHierarchy)
            .where(
                EmployeeHierarchy.ancestor_id == target_id,
                EmployeeHierarchy.descendant_id == other_id,
            )
            .where(EmployeeHierarchy.depth >= int(not same))
        )
        return self.session.scalar(exec) is not None

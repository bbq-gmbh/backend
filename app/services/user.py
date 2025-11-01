from typing import Optional

from app.core.security import verify_password
from app.models.employee import Employee
from app.models.user import User

from app.repositories.user import UserRepository
from app.core.exceptions import (
    UserAlreadyExistsError,
    UserNotAuthorizedError,
    ValidationError,
    InvalidCredentialsError,
)
from app.schemas.query import PagedResult
from app.schemas.user import UserCreate, UserEmployeeOnly, UserInfo, UserOnly


class UserService:
    def __init__(self, *, user_repo: UserRepository):
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

    def delete_user(self, actor: User, user: User):
        # TODO

        if not actor.is_superuser:
            raise UserNotAuthorizedError()

        if user.employee:
            pass

        self.user_repo.delete_user(user)

        self.session.commit()
        self.session.refresh(user)

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

    def get_users(self, page: int, page_size: int) -> list[User]:
        if page_size <= 0:
            raise ValidationError("Page Size must be greater than 0")
        if page < 0:
            raise ValidationError("Page must be non negative")

        return self.user_repo.get_users(page, page_size)

    def get_user_employee_pairs(
        self, page: int, page_size: int
    ) -> PagedResult[list[tuple[User, Optional[Employee]]]]:
        if page_size <= 0:
            raise ValidationError("Page Size must be greater than 0")
        if page < 0:
            raise ValidationError("Page must be non negative")

        return PagedResult(
            page=self.user_repo.get_user_employee_pairs(page, page_size),
            total=self.user_repo.get_user_employee_pairs_count(),
        )

    def get_lower_user_employee_pairs_paged(
        self, employee: Employee, page: int, page_size: int
    ) -> PagedResult[list[tuple[User, Employee]]]:
        if page_size <= 0:
            raise ValidationError("Page Size must be greater than 0")
        if page < 0:
            raise ValidationError("Page must be non negative")

        return PagedResult(
            page=self.user_repo.get_lower_user_employee_pairs_paged(
                employee, page, page_size, same=True
            ),
            total=self.user_repo.get_lower_user_employee_pairs_paged_count(
                employee, same=True
            ),
        )

    def get_visible_user_employee_pairs(
        self, actor: User, page: int, page_size: int
    ) -> PagedResult[list[tuple[User, Optional[Employee]]]]:
        if actor.is_superuser:
            return self.get_user_employee_pairs(page, page_size)

        if actor.employee:
            return PagedResult(
                page=self.user_repo.get_lower_user_employee_pairs_paged(
                    actor.employee, page, page_size
                ),
                total=self.user_repo.get_lower_user_employee_pairs_paged_count(
                    actor.employee
                ),
            )  # type: ignore

        if page_size <= 0:
            raise ValidationError("Page Size must be greater than 0")
        if page < 0:
            raise ValidationError("Page must be non negative")

        return PagedResult(page=[(actor, actor.employee)], total=1)

    @staticmethod
    def _user_to_user_only(user: User) -> UserOnly:
        return UserOnly(
            id=user.id,
            username=user.username,
            is_superuser=user.is_superuser,
            created_at=user.created_at,
        )

    @staticmethod
    def _employee_to_employee_only(employee: Employee) -> UserEmployeeOnly:
        return UserEmployeeOnly(
            first_name=employee.first_name,
            last_name=employee.last_name,
        )

    @staticmethod
    def _user_employee_pair_to_user_info(
        user: User, employee: Employee | None
    ) -> UserInfo:
        return UserInfo(
            id=user.id,
            username=user.username,
            is_superuser=user.is_superuser,
            created_at=user.created_at,
            employee=UserService._employee_to_employee_only(employee)
            if employee
            else None,
        )

from typing import Optional

from app.core.exceptions import EmployeeAlreadyExistsError, UserNotFoundError
from app.models.employee import Employee
from app.repositories.employee import EmployeeRepository
from app.schemas.employee import EmployeeCreate


class EmployeeService:
    def __init__(self, employee_repo: EmployeeRepository):
        self.employee_repo = employee_repo
        self.user_repo = employee_repo.user_repo
        self.session = self.user_repo.session

    def create_employee_for_user(self, employee_in: EmployeeCreate) -> Employee:
        user = self.user_repo.get_user_by_id(employee_in.user_id)
        if not user:
            raise UserNotFoundError(user_id=employee_in.user_id)

        if user.employee:
            raise EmployeeAlreadyExistsError()

        user.employee = self.employee_repo.create_employee(employee_in)
        self.session.add(user.employee)
        self.session.add(user)

        self.session.commit()
        self.session.refresh(user.employee)
        return user.employee

    def get_employee_by_user_id(self, user_id: str) -> Optional[Employee]:
        user = self.user_repo.get_user_by_id(user_id)
        if not user:
            raise UserNotFoundError(user_id=user_id)
        return user.employee

from typing import Optional

from app.config.settings import Settings
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
            raise UserNotFoundError(user_id=employee_in.user_id)  # type: ignore TODO

        if user.employee:
            raise EmployeeAlreadyExistsError()

        user.employee = self.employee_repo.create_employee(employee_in)
        self.session.add(user.employee)
        self.session.add(user)

        self.session.commit()
        self.session.refresh(user.employee)
        return user.employee

    def get_employee_by_user_id(self, user_id: str) -> Optional[Employee]:
        user = self.user_repo.get_user_by_id(user_id)  # type: ignore TODO
        if not user:
            raise UserNotFoundError(user_id=user_id)
        return user.employee

    def get_hirarchy_difference(
        self, employee: Employee, other: Employee
    ) -> Optional[int]:
        """Calculate the hierarchy level difference between two employees.

        Args:
            employee: The employee to check.
            other: The employee to compare against.

        Returns:
            Positive int if employee is higher, 0 if same, negative if lower, None if not related.
        """
        # Check if they are the same employee
        if employee.user_id == other.user_id:
            return 0

        # Check if employee is a supervisor of other (going up from other)
        current = other
        for level in range(1, Settings.EMPLOYEE_MAX_HIRARCHY_LEVELS + 1):
            if current.supervisor_id is None:
                break
            if current.supervisor_id == employee.user_id:
                return level
            current = current.supervisor
            if current is None:
                break

        # Check if employee is a subordinate of other (going up from employee)
        current = employee
        for level in range(-1, -(Settings.EMPLOYEE_MAX_HIRARCHY_LEVELS + 1), -1):
            if current.supervisor_id is None:
                break
            if current.supervisor_id == other.user_id:
                return level
            current = current.supervisor
            if current is None:
                break

        # Not related
        return None

    def is_related_to(self, employee: Employee, other: Employee) -> bool:
        """Check if two employees are related in the hierarchy.

        Args:
            employee: The employee to check.
            other: The employee to compare against.

        Returns:
            True if they are the same or one is a supervisor/subordinate of the other, False otherwise.
        """
        return self.get_hirarchy_difference(employee, other) is not None

    def is_higher(
        self, employee: Employee, other: Employee, same: bool = False
    ) -> bool:
        """Check if 'employee' is higher in the hierarchy than 'other'.

        Args:
            employee: The employee to check.
            other: The employee to compare against.
            same: If True, returns True when employees are the same. Default is False.

        Returns:
            True if employee is a supervisor of other (or same when same=True), False otherwise.
        """
        # Check if they are the same employee
        if employee.user_id == other.user_id:
            return same

        # Check if employee is a supervisor of other (going up from other)
        current = other
        for _ in range(Settings.EMPLOYEE_MAX_HIRARCHY_LEVELS):
            if current.supervisor_id is None:
                break
            if current.supervisor_id == employee.user_id:
                return True
            current = current.supervisor
            if current is None:
                break

        return False

    def is_lower(self, employee: Employee, other: Employee, same: bool = False) -> bool:
        """Check if 'employee' is lower in the hierarchy than 'other'.

        Args:
            employee: The employee to check.
            other: The employee to compare against.
            same: If True, returns True when employees are the same. Default is False.

        Returns:
            True if employee is a subordinate of other (or same when same=True), False otherwise.
        """
        # Check if they are the same employee
        if employee.user_id == other.user_id:
            return same

        # Check if employee is a subordinate of other (going up from employee)
        current = employee
        for _ in range(Settings.EMPLOYEE_MAX_HIRARCHY_LEVELS):
            if current.supervisor_id is None:
                break
            if current.supervisor_id == other.user_id:
                return True
            current = current.supervisor
            if current is None:
                break

        return False

    def is_supervisor_of(self, employee: Employee, other: Employee) -> bool:
        return False

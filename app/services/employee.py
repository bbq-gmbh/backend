import uuid
from typing import Optional

from app.config.settings import Settings
from app.core.exceptions import (
    DomainError,
    EmployeeAlreadyExistsError,
    HierarchyCycleError,
    HierarchyDepthExceededError,
    InvalidSupervisorAssignmentError,
    UserNotFoundError,
)
from app.models.employee import Employee
from app.repositories.employee import EmployeeRepository
from app.repositories.employee_hierarchy import EmployeeHierarchyRepository
from app.repositories.user import UserRepository
from app.schemas.employee import EmployeeCreate


class EmployeeService:
    def __init__(
        self,
        employee_repo: EmployeeRepository,
        employee_hierarchy_repo: EmployeeHierarchyRepository,
        user_repo: UserRepository,
    ):
        self.employee_repo = employee_repo
        self.hierarchy_repo = employee_hierarchy_repo
        self.user_repo = user_repo
        self.session = user_repo.session

    def create_employee_for_user(self, employee_in: EmployeeCreate) -> Employee:
        user = self.user_repo.get_user_by_id(employee_in.user_id)
        if not user:
            raise UserNotFoundError(user_id=employee_in.user_id)

        if user.employee:
            raise EmployeeAlreadyExistsError()

        employee = Employee(
            user_id=employee_in.user_id,
            first_name=employee_in.first_name,
            last_name=employee_in.last_name,
        )
        user.employee = employee

        self.hierarchy_repo.add_self_reference(employee)

        self.session.commit()
        self.session.refresh(employee)
        return employee

    def assign_supervisor_to_employee(
        self, target: Employee, supervisor: Employee
    ) -> None:
        self._validate_supervisor_assignment(target, supervisor)

        if target.supervisor_id:
            self.remove_supervisor_from_employee(target)

        target.supervisor_id = supervisor.user_id
        target.supervisor = supervisor

        ancestor_ids = self.hierarchy_repo.get_ancestor_ids(
            supervisor.user_id, include_self=True
        )
        descendant_ids = self.hierarchy_repo.get_descendant_ids(
            target.user_id, include_self=True
        )

        self.hierarchy_repo.insert_hierarchy_paths(ancestor_ids, descendant_ids)

        self.session.commit()

    def remove_supervisor_from_employee(self, target: Employee) -> None:
        if not target.supervisor_id:
            return

        ancestor_ids = self.hierarchy_repo.get_ancestor_ids(target.user_id)
        descendant_ids = self.hierarchy_repo.get_descendant_ids(
            target.user_id, include_self=True
        )

        self.hierarchy_repo.delete_hierarchy_paths(ancestor_ids, descendant_ids)

        target.supervisor_id = None
        target.supervisor = None

        self.session.commit()

    def _validate_supervisor_assignment(
        self, target: Employee, supervisor: Employee
    ) -> None:
        if target.user_id == supervisor.user_id:
            raise InvalidSupervisorAssignmentError(
                "Employee cannot be their own supervisor"
            )

        if self.would_create_cycle(target, supervisor):
            raise HierarchyCycleError(
                f"Assigning {supervisor.user_id} as supervisor of "
                f"{target.user_id} would create a cycle"
            )

        supervisor_depth = self._get_depth(supervisor)
        target_subtree_depth = self._get_subtree_depth(target)

        max_depth = Settings.EMPLOYEE_MAX_HIRARCHY_LEVELS
        if supervisor_depth + target_subtree_depth + 1 > max_depth:
            raise HierarchyDepthExceededError(
                f"Assignment would exceed maximum hierarchy depth of {max_depth}"
            )

    def would_create_cycle(self, target: Employee, supervisor: Employee) -> bool:
        subordinate_ids = self.hierarchy_repo.get_descendant_ids(target.user_id)
        return supervisor.user_id in subordinate_ids

    def _get_depth(self, employee: Employee) -> int:
        ancestor_ids = self.hierarchy_repo.get_ancestor_ids(
            employee.user_id, include_self=False
        )
        return len(ancestor_ids)

    def _get_subtree_depth(self, employee: Employee) -> int:
        descendants = self.hierarchy_repo.get_subordinates(
            employee.user_id, include_self=True
        )
        if not descendants:
            return 0

        max_depth = 0
        employee_depth = self._get_depth(employee)

        for desc in descendants:
            depth = self._get_depth(desc) - employee_depth
            max_depth = max(max_depth, depth)

        return max_depth

    def is_supervisor_of(
        self,
        potential_supervisor: Employee,
        potential_subordinate: Employee,
        include_self: bool = False,
    ) -> bool:
        if (
            include_self
            and potential_supervisor.user_id == potential_subordinate.user_id
        ):
            return True

        ancestor_ids = self.hierarchy_repo.get_ancestor_ids(
            potential_subordinate.user_id, include_self=False
        )
        return potential_supervisor.user_id in ancestor_ids

    def get_hierarchy_level_difference(
        self, employee1: Employee, employee2: Employee
    ) -> Optional[int]:
        if employee1.user_id == employee2.user_id:
            return 0

        if self.is_supervisor_of(employee1, employee2):
            depth1 = self._get_depth(employee1)
            depth2 = self._get_depth(employee2)
            return depth2 - depth1

        if self.is_supervisor_of(employee2, employee1):
            depth1 = self._get_depth(employee1)
            depth2 = self._get_depth(employee2)
            return depth2 - depth1

        return None

    def get_employee_by_user_id(self, user_id: uuid.UUID) -> Optional[Employee]:
        user = self.user_repo.get_user_by_id(user_id)
        if not user:
            raise UserNotFoundError(user_id=user_id)
        return user.employee

    @staticmethod
    def safe_get_hirarchy_difference(
        employee: Employee, other: Employee
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

    @staticmethod
    def safe_is_related_to(employee: Employee, other: Employee) -> bool:
        """Check if two employees are related in the hierarchy.

        Args:
            employee: The employee to check.
            other: The employee to compare against.

        Returns:
            True if they are the same or one is a supervisor/subordinate of the other, False otherwise.
        """
        return EmployeeService.safe_get_hirarchy_difference(employee, other) is not None

    @staticmethod
    def safe_is_higher(
        employee: Employee, other: Employee, *, same: bool = False
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

    @staticmethod
    def safe_is_lower(
        employee: Employee, other: Employee, *, same: bool = False
    ) -> bool:
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

    def remove_supervisor(self, target: Employee, *, force: bool = False) -> None:
        """DEPRECATED: Use remove_supervisor_from_employee() instead.

        This method will be removed in a future version.
        """
        if not target.supervisor and not force:
            return

        target.supervisor = None
        self.hierarchy_repo.remove_supervisor(target)

    def assign_supervisor(self, target: Employee, supervisor: Employee) -> None:
        """DEPRECATED: Use assign_supervisor_to_employee() instead.

        This method will be removed in a future version.
        """
        if target.supervisor:
            raise DomainError("Cannot assign supervisor because it was not None")

        target.supervisor = supervisor
        self.hierarchy_repo.assign_supervisor(target, supervisor)

import uuid
from typing import Any

from sqlalchemy import func
from sqlmodel import Session, delete, select

from app.models.employee import Employee
from app.models.employee_hierarchy import EmployeeHierarchy
from app.models.user import User


class EmployeeHierarchyRepository:
    def __init__(self, session: Session):
        self.session = session

    # ========================================================================
    # NEW METHODS - Clean, single-responsibility data access
    # ========================================================================

    def add_self_reference(self, employee: Employee) -> None:
        """Add self-reference entry (depth=0) for an employee.

        This is the base entry in the closure table that every employee needs.

        Args:
            employee: The employee to add self-reference for
        """
        element = EmployeeHierarchy(
            ancestor_id=employee.user_id, descendant_id=employee.user_id, depth=0
        )
        self.session.add(element)

    def delete_hierarchy_paths(
        self, ancestor_ids: list[uuid.UUID], descendant_ids: list[uuid.UUID]
    ) -> None:
        """Delete specific paths from hierarchy table.

        Removes all paths between the given ancestors and descendants.

        Args:
            ancestor_ids: List of ancestor user IDs
            descendant_ids: List of descendant user IDs
        """
        if not ancestor_ids or not descendant_ids:
            return

        exec_del = delete(EmployeeHierarchy).where(
            EmployeeHierarchy.ancestor_id.in_(ancestor_ids),  # type: ignore
            EmployeeHierarchy.descendant_id.in_(descendant_ids),  # type: ignore
        )
        self.session.exec(exec_del)

    def insert_hierarchy_paths(
        self, ancestor_ids: list[uuid.UUID], descendant_ids: list[uuid.UUID]
    ) -> None:
        """Insert new paths into hierarchy table.

        Creates all combinations of ancestors and descendants with correct depths.
        The depth is calculated as: ancestor_depth + descendant_depth + 1

        Args:
            ancestor_ids: List of ancestor user IDs (ordered by depth)
            descendant_ids: List of descendant user IDs (ordered by depth)
        """
        if not ancestor_ids or not descendant_ids:
            return

        paths = []
        for i, ancestor_id in enumerate(ancestor_ids):
            for j, descendant_id in enumerate(descendant_ids):
                paths.append(
                    EmployeeHierarchy(
                        ancestor_id=ancestor_id,
                        descendant_id=descendant_id,
                        depth=i + j + 1,
                    )
                )

        if paths:
            self.session.add_all(paths)

    def clear_all_hierarchy(self) -> int:
        """Delete all hierarchy records.

        WARNING: This removes ALL entries from the closure table.
        Use with caution, typically only for rebuild operations.

        Returns:
            Number of records deleted
        """
        result = self.session.exec(delete(EmployeeHierarchy))
        return result.rowcount  # type: ignore

    def get_ancestor_ids(
        self, descendant_id: uuid.UUID, include_self: bool = False
    ) -> list[uuid.UUID]:
        """Get all ancestor IDs for a given employee.

        Args:
            descendant_id: The employee's user ID
            include_self: Whether to include the employee themselves

        Returns:
            List of ancestor IDs, ordered by depth (closest first)
        """
        stmt = (
            select(EmployeeHierarchy.ancestor_id)
            .where(EmployeeHierarchy.descendant_id == descendant_id)
            .where(EmployeeHierarchy.depth >= int(not include_self))
            .order_by(EmployeeHierarchy.depth.asc())  # type: ignore
        )
        return list(self.session.scalars(stmt).all())

    def get_descendant_ids(
        self, ancestor_id: uuid.UUID, include_self: bool = False
    ) -> list[uuid.UUID]:
        """Get all descendant IDs for a given employee.

        Args:
            ancestor_id: The employee's user ID
            include_self: Whether to include the employee themselves

        Returns:
            List of descendant IDs, ordered by depth (closest first)
        """
        stmt = (
            select(EmployeeHierarchy.descendant_id)
            .where(EmployeeHierarchy.ancestor_id == ancestor_id)
            .where(EmployeeHierarchy.depth >= int(not include_self))
            .order_by(EmployeeHierarchy.depth.asc())  # type: ignore
        )
        return list(self.session.scalars(stmt).all())

    def get_subordinates(
        self, supervisor_id: uuid.UUID, include_self: bool = False
    ) -> list[Employee]:
        """Get all subordinate employees (direct and indirect).

        Args:
            supervisor_id: The supervisor's user ID
            include_self: Whether to include the supervisor themselves

        Returns:
            List of subordinate Employee objects
        """
        stmt = (
            select(Employee)
            .join(
                EmployeeHierarchy,
                Employee.user_id == EmployeeHierarchy.descendant_id,  # type: ignore
            )
            .where(EmployeeHierarchy.ancestor_id == supervisor_id)
            .where(EmployeeHierarchy.depth >= int(not include_self))
        )
        return list(self.session.scalars(stmt).all())

    def get_supervisors(
        self, subordinate_id: uuid.UUID, include_self: bool = False
    ) -> list[Employee]:
        """Get all supervisor employees (direct and indirect).

        Args:
            subordinate_id: The subordinate's user ID
            include_self: Whether to include the subordinate themselves

        Returns:
            List of supervisor Employee objects
        """
        stmt = (
            select(Employee)
            .join(
                EmployeeHierarchy,
                Employee.user_id == EmployeeHierarchy.ancestor_id,  # type: ignore
            )
            .where(EmployeeHierarchy.descendant_id == subordinate_id)
            .where(EmployeeHierarchy.depth >= int(not include_self))
        )
        return list(self.session.scalars(stmt).all())

    def get_all_employees(self) -> list[Employee]:
        """Get all employees from the database.

        Returns:
            List of all Employee objects
        """
        return list(self.session.exec(select(Employee)).all())

    def get_employee_by_id(self, user_id: uuid.UUID) -> Employee | None:
        """Get employee by user_id.

        Args:
            user_id: The employee's user ID

        Returns:
            Employee object or None if not found
        """
        return self.session.get(Employee, user_id)

    def find_orphaned_employees(self) -> list[Employee]:
        """Find employees with supervisor_id pointing to non-existent employee.

        Returns:
            List of orphaned Employee objects
        """
        stmt = (
            select(Employee)
            .where(Employee.supervisor_id.isnot(None))  # type: ignore
            .where(
                Employee.supervisor_id.not_in(  # type: ignore
                    select(Employee.user_id)
                )
            )
        )
        return list(self.session.scalars(stmt).all())

    def get_hierarchy_statistics(self) -> dict[str, Any]:
        """Get basic statistics about hierarchy structure.

        Returns:
            Dictionary with statistics including:
            - total_employees: Total number of employees
            - total_hierarchy_records: Total closure table entries
            - max_depth: Maximum depth in hierarchy
            - avg_depth: Average depth across all paths
            - employees_without_supervisor: Count of top-level employees
        """
        total_employees = (
            self.session.scalar(select(func.count()).select_from(Employee)) or 0
        )

        total_records = (
            self.session.scalar(select(func.count()).select_from(EmployeeHierarchy))
            or 0
        )

        max_depth = self.session.scalar(select(func.max(EmployeeHierarchy.depth))) or 0

        avg_depth = (
            self.session.scalar(select(func.avg(EmployeeHierarchy.depth))) or 0.0
        )

        employees_without_supervisor = (
            self.session.scalar(
                select(func.count())
                .select_from(Employee)
                .where(
                    Employee.supervisor_id.is_(None)  # type: ignore
                )
            )
            or 0
        )

        return {
            "total_employees": total_employees,
            "total_hierarchy_records": total_records,
            "max_depth": max_depth,
            "avg_depth": float(avg_depth),
            "employees_without_supervisor": employees_without_supervisor,
        }

    # ========================================================================
    # OLD METHODS - Kept for backward compatibility, will be deprecated
    # ========================================================================

    def add_to_hirarchy(self, target: Employee):
        element = EmployeeHierarchy(
            ancestor_id=target.user_id, descendant_id=target.user_id, depth=0
        )
        self.session.add(element)

    def get_lower(self, target: Employee, *, same: bool = False) -> list[Employee]:
        exec = (
            select(Employee)
            .join(
                EmployeeHierarchy,
                Employee.user_id == EmployeeHierarchy.descendant_id,  # type: ignore
            )
            .where(EmployeeHierarchy.ancestor_id == target.user_id)
            .where(EmployeeHierarchy.depth >= int(not same))
        )

        result = self.session.scalars(exec)
        return list(result.all())

    def get_higher(self, target: Employee, *, same: bool = False) -> list[Employee]:
        exec = (
            select(Employee)
            .join(
                EmployeeHierarchy,
                Employee.user_id == EmployeeHierarchy.ancestor_id,  # type: ignore
            )
            .where(EmployeeHierarchy.descendant_id == target.user_id)
            .where(EmployeeHierarchy.depth >= int(not same))
        )

        result = self.session.scalars(exec)
        return list(result.all())

    def get_lower_users(self, target: Employee, *, same: bool = False) -> list[User]:
        exec = (
            select(User)
            .join(Employee)
            .join(
                EmployeeHierarchy,
                Employee.user_id == EmployeeHierarchy.descendant_id,  # type: ignore
            )
            .where(EmployeeHierarchy.ancestor_id == target.user_id)
            .where(EmployeeHierarchy.depth >= int(not same))
        )

        result = self.session.scalars(exec)
        return list(result.all())

    def get_higher_users(self, target: Employee, *, same: bool = False) -> list[User]:
        exec = (
            select(User)
            .join(Employee)
            .join(
                EmployeeHierarchy,
                Employee.user_id == EmployeeHierarchy.ancestor_id,  # type: ignore
            )
            .where(EmployeeHierarchy.descendant_id == target.user_id)
            .where(EmployeeHierarchy.depth >= int(not same))
        )

        result = self.session.scalars(exec)
        return list(result.all())

    def get_lower_user_ids(
        self, target: Employee, *, same: bool = False
    ) -> list[uuid.UUID]:
        exec = (
            select(EmployeeHierarchy.descendant_id)
            .where(EmployeeHierarchy.ancestor_id == target.user_id)
            .where(EmployeeHierarchy.depth >= int(not same))
        )

        result = self.session.scalars(exec)
        return list(result.all())

    def get_higher_user_ids(
        self, target: Employee, *, same: bool = False
    ) -> list[uuid.UUID]:
        exec = (
            select(EmployeeHierarchy.ancestor_id)
            .where(EmployeeHierarchy.descendant_id == target.user_id)
            .where(EmployeeHierarchy.depth >= int(not same))
        )

        result = self.session.scalars(exec)
        return list(result.all())

    def remove_supervisor(self, target: Employee):
        ids_upper = self.get_higher_user_ids(target)
        ids_lower = self.get_lower_user_ids(target, same=True)

        exec_del = delete(EmployeeHierarchy).where(
            EmployeeHierarchy.ancestor_id.in_(ids_upper),  # type: ignore
            EmployeeHierarchy.descendant_id.in_(ids_lower),  # type: ignore
        )
        self.session.exec(exec_del)

        target.supervisor = None

    def assign_supervisor(self, target: Employee, supervisor: Employee):
        exec_super = (
            select(EmployeeHierarchy.ancestor_id)
            .where(EmployeeHierarchy.descendant_id == supervisor.user_id)
            .order_by(EmployeeHierarchy.depth.asc())  # type: ignore
        )
        result_super = self.session.scalars(exec_super)
        all_super = list(result_super.all())

        exec_lower = (
            select(EmployeeHierarchy.descendant_id)
            .where(EmployeeHierarchy.ancestor_id == target.user_id)
            .order_by(EmployeeHierarchy.depth.asc())  # type: ignore
        )
        result_lower = self.session.scalars(exec_lower)
        all_lower = list(result_lower.all())

        all = []
        for i, super in enumerate(all_super):
            for j, lower in enumerate(all_lower):
                all.append(
                    EmployeeHierarchy(
                        ancestor_id=super, descendant_id=lower, depth=i + j + 1
                    )
                )

        self.session.add_all(all)

        target.supervisor = supervisor

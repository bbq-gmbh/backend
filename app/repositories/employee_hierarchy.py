import uuid
from typing import Any

from sqlalchemy import func
from sqlmodel import Session, delete, select

from app.models.employee import Employee
from app.models.employee_hierarchy import EmployeeHierarchy


class EmployeeHierarchyRepository:
    def __init__(self, session: Session):
        self.session = session

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

    def delete_hierarchy_paths_for_employee(self, user_id: uuid.UUID) -> None:
        """Delete all hierarchy paths involving an employee.
        
        This removes all records where the employee appears as either ancestor or descendant.
        Used when completely removing an employee from the hierarchy.
        
        Args:
            user_id: The employee's user ID to remove from hierarchy
        """
        # Delete where employee is ancestor (all their subordinates)
        exec_del_ancestor = delete(EmployeeHierarchy).where(
            EmployeeHierarchy.ancestor_id == user_id  # type: ignore
        )
        self.session.exec(exec_del_ancestor)
        
        # Delete where employee is descendant (all their supervisors)
        exec_del_descendant = delete(EmployeeHierarchy).where(
            EmployeeHierarchy.descendant_id == user_id  # type: ignore
        )
        self.session.exec(exec_del_descendant)

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

    def rebuild_hierarchy_full(self) -> dict[str, int]:
        """Completely rebuild the employee hierarchy table.
        
        This method:
        1. Deletes all records from employee_hierarchy table
        2. For each employee, adds self-reference (depth=0)
        3. For each employee, traverses supervisor chain to create all paths
        
        Returns:
            Dictionary with statistics:
            - records_deleted: Number of old records removed
            - records_created: Number of new records created
            - employees_processed: Number of employees processed
        """
        # Step 1: Clear all existing hierarchy records
        records_deleted = self.clear_all_hierarchy()
        
        # Step 2: Get all employees
        all_employees = self.get_all_employees()
        employees_processed = len(all_employees)
        records_created = 0
        
        # Create a map for quick employee lookup
        employee_map = {emp.user_id: emp for emp in all_employees}
        
        # Step 3: Add self-references for all employees
        for employee in all_employees:
            self.add_self_reference(employee)
            records_created += 1
        
        # Step 4: For each employee, create paths to all ancestors
        for employee in all_employees:
            if employee.supervisor_id:
                # Traverse up the supervisor chain
                current_id = employee.supervisor_id
                depth = 1
                
                while current_id is not None and depth <= 100:  # Safety limit
                    # Create hierarchy entry
                    hierarchy_entry = EmployeeHierarchy(
                        ancestor_id=current_id,
                        descendant_id=employee.user_id,
                        depth=depth,
                    )
                    self.session.add(hierarchy_entry)
                    records_created += 1
                    
                    # Move up to next supervisor
                    current_emp = employee_map.get(current_id)
                    if current_emp and current_emp.supervisor_id:
                        current_id = current_emp.supervisor_id
                        depth += 1
                    else:
                        break
        
        # Commit all changes
        self.session.flush()
        
        return {
            "records_deleted": records_deleted,
            "records_created": records_created,
            "employees_processed": employees_processed,
        }

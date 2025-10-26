import uuid

from sqlmodel import Session, delete, select

from app.models.employee import Employee
from app.models.employee_hierarchy import EmployeeHierarchy
from app.models.user import User


class EmployeeHierarchyRepository:
    def __init__(self, session: Session):
        self.session = session

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
            select(User.id)
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

    def get_higher_user_ids(
        self, target: Employee, *, same: bool = False
    ) -> list[uuid.UUID]:
        exec = (
            select(User.id)
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

    def remove_supervisor(self, target: Employee):
        if not target.supervisor:
            return

        ids_upper = self.get_higher_user_ids(target)
        ids_lower = self.get_lower_user_ids(target, same=True)

        exec_del = delete(EmployeeHierarchy).where(
            EmployeeHierarchy.ancestor_id.in_(ids_upper),  # type: ignore
            EmployeeHierarchy.descendant_id.in_(ids_lower),  # type: ignore
        )
        self.session.exec(exec_del)

        target.supervisor = None

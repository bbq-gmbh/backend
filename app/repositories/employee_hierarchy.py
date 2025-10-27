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
        if not target.supervisor:
            raise ValueError("target must have an assigned supervisor")

        ids_upper = self.get_higher_user_ids(target)
        ids_lower = self.get_lower_user_ids(target, same=True)

        exec_del = delete(EmployeeHierarchy).where(
            EmployeeHierarchy.ancestor_id.in_(ids_upper),  # type: ignore
            EmployeeHierarchy.descendant_id.in_(ids_lower),  # type: ignore
        )
        self.session.exec(exec_del)

        target.supervisor = None

    def assign_supervisor(self, target: Employee, supervisor: Employee):
        if target.supervisor:
            raise ValueError("target must not have an assigned supervisor")

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

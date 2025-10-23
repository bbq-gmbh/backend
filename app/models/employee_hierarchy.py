import uuid
from typing import TYPE_CHECKING

from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from .employee import Employee


class EmployeeHierarchy(SQLModel, table=True):
    __tablename__: str = "employee_hierarchy"

    ancestor_id: uuid.UUID = Field(
        primary_key=True,
        foreign_key="employees.user_id",
    )
    descendant_id: uuid.UUID = Field(
        primary_key=True,
        foreign_key="employees.user_id",
    )
    depth: int = Field(ge=1)

    ancestor: "Employee" = Relationship(
        sa_relationship_kwargs={"foreign_keys": "EmployeeHierarchy.ancestor_id"}
    )
    descendant: "Employee" = Relationship(
        sa_relationship_kwargs={"foreign_keys": "EmployeeHierarchy.descendant_id"}
    )

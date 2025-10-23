import uuid
from sqlmodel import Field, SQLModel


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

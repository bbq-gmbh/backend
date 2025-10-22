import uuid
from typing import TYPE_CHECKING, Optional
from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from .user import User


class Employee(SQLModel, table=True):
    __tablename__: str = "employees"
    user_id: uuid.UUID = Field(primary_key=True, foreign_key="users.id")
    first_name: str
    last_name: str
    supervisor_id: Optional[uuid.UUID] = Field(
        default=None, foreign_key="employees.user_id", index=True
    )

    user: "User" = Relationship(back_populates="employee")
    supervisor: Optional["Employee"] = Relationship(back_populates="subordinates")
    subordinates: list["Employee"] = Relationship(back_populates="supervisor")

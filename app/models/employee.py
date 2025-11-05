import uuid

from datetime import date
from enum import Enum
from typing import TYPE_CHECKING, Optional

from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from .user import User


class HourModel(Enum):
    e30 = 6
    e35 = 7
    e40 = 8


class Employee(SQLModel, table=True):
    __tablename__: str = "employees"
    user_id: uuid.UUID = Field(primary_key=True, foreign_key="users.id")
    first_name: str
    last_name: str
    supervisor_id: Optional[uuid.UUID] = Field(
        default=None, foreign_key="employees.user_id", index=True
    )
    birthday: date
    hour_model: HourModel
    pause_time_minutes: int
    start_from: date

    user: "User" = Relationship(back_populates="employee")
    supervisor: Optional["Employee"] = Relationship(
        back_populates="subordinates",
        sa_relationship_kwargs={"remote_side": "Employee.user_id"},
    )
    subordinates: list["Employee"] = Relationship(back_populates="supervisor")

import uuid
from typing import TYPE_CHECKING
from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from .user import User


class Employee(SQLModel, table=True):
    __tablename__: str = "employees"
    user_id: uuid.UUID = Field(primary_key=True, foreign_key="users.id")
    first_name: str
    last_name: str

    user: "User" = Relationship(back_populates="employee")

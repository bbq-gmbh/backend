import uuid
from typing import TYPE_CHECKING, Optional
from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from .user import User


class Employee(SQLModel, table=True):
    __tablename__: str = "employees"
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    first_name: str
    last_name: str
    age: Optional[int] = Field(default=None, description="Employee age for break calculation")

    user: "User" = Relationship(back_populates="employee")

import uuid
from typing import Optional, TYPE_CHECKING
from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from .user import User


class Employee(SQLModel, table=True):
    __tablename__: str = "employees"
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    first_name: str
    last_name: str

    user: Optional["User"] = Relationship(back_populates="employee")

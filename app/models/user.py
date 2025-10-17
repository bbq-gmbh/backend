import uuid
from typing import Optional, TYPE_CHECKING
from datetime import datetime, timezone

from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from .employee import Employee

from .employee import Employee


class User(SQLModel, table=True):
    __tablename__: str = "users"
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    username: str = Field(unique=True, index=True)
    password_hash: str
    token_key: uuid.UUID = Field(default_factory=uuid.uuid4, index=True)
    is_superuser: bool = Field(default=False)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column_kwargs={"onupdate": lambda: datetime.now(timezone.utc)},
    )

    employee_id: Optional[uuid.UUID] = Field(
        default=None, foreign_key="employees.user_id", unique=True
    )
    employee: Optional["Employee"] = Relationship(back_populates="user")

import uuid
from enum import Enum
from typing import TYPE_CHECKING, Optional
from datetime import datetime, timezone

from sqlmodel import Field, Relationship, SQLModel
from sqlalchemy.orm import relationship

if TYPE_CHECKING:
    from .employee import Employee
    from .user import User


class TimeEntryType(Enum):
    Arrival = "arrival"
    Departure = "departure"


class TimeEntry(SQLModel, table=True):
    __tablename__: str = "time_entries"
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: uuid.UUID = Field(foreign_key="employees.user_id", index=True)
    entry_type: TimeEntryType
    date_time: datetime = Field(index=True)
    created_by: uuid.UUID = Field(foreign_key="users.id", index=True)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc), index=True
    )
    updated_by: Optional[uuid.UUID] = Field(
        default=None, foreign_key="users.id", index=True
    )
    last_updated: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column_kwargs={"onupdate": datetime.now(timezone.utc)},
        index=True,
    )

    employee: "Employee" = Relationship(
        sa_relationship=relationship(foreign_keys=[user_id])  # type: ignore
    )
    creator: "User" = Relationship(
        sa_relationship=relationship(foreign_keys=[created_by])  # type: ignore
    )
    updater: Optional["User"] = Relationship(
        sa_relationship=relationship(foreign_keys=[updated_by])  # type: ignore
    )

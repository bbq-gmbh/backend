import uuid

from enum import Enum
from datetime import date, datetime, timezone
from typing import TYPE_CHECKING, Optional

from sqlmodel import Field, Relationship, SQLModel


if TYPE_CHECKING:
    from .employee import Employee
    from .user import User


class AbsenceEntryType(Enum):
    Sickness = "sickness"
    Holiday = "holiday"
    Other = "other"


class AbsenceEntry(SQLModel, table=True):
    __tablename__: str = "time_entries"
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: uuid.UUID = Field(foreign_key="employees.user_id", index=True)
    entry_type: AbsenceEntryType
    
    date_begin: date = Field(index=True)
    date_end: date = Field(index=True)

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
        sa_relationship_kwargs={"foreign_keys": "AbsenceEntry.user_id"}
    )
    creator: "User" = Relationship(
        sa_relationship_kwargs={"foreign_keys": "AbsenceEntry.created_by"}
    )
    updater: Optional["User"] = Relationship(
        sa_relationship_kwargs={"foreign_keys": "AbsenceEntry.updated_by"}
    )

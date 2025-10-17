from enum import Enum
from typing import Optional
from datetime import datetime, timezone

from sqlmodel import Field, SQLModel


class TimeEntryType(Enum):
    Arrival = "arrival"
    Departure = "departure"


class TimeEntry(SQLModel, table=True):
    __tablename__: str = "time_entries"
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: str = Field(foreign_key="employees.id", index=True)
    author_id: str = Field(foreign_key="users.id", index=True)
    entry_type: TimeEntryType
    date_time: datetime = Field(index=True)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc), index=True
    )
    last_updated: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column_kwargs={"onupdate": datetime.now(timezone.utc)},
        index=True,
    )

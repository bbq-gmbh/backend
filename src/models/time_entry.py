from sqlmodel import create_engine, Field, Relationship, SQLModel, Session
import os
from pathlib import Path
from dotenv import load_dotenv
import uuid
from datetime import datetime, timezone, time
from enum import Enum
from sqlalchemy import Column, ForeignKey, Enum as SAEnum
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from .employee import Employee

class TimeRecordType(Enum):
    Arrival = "arrival"
    Departure = "departure"


class TimeEntry(SQLModel, table=True):
    id: int = Field(primary_key=True, index=True)
    employee_id: uuid.UUID = Field(foreign_key="employee.id", index=True)
    date_time: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), index=True)
    type: TimeRecordType
    last_updated: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column_kwargs={"onupdate": lambda: datetime.now(timezone.utc)}
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc))
    updated_by: Optional[uuid.UUID] = Field(default=None)
    
    
    employee: "Employee" = Relationship(back_populates="time_entries")
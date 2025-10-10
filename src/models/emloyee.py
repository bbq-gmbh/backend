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
    from .user_nd import User
    from .time_entry_nd import TimeEntry


class Employee(SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    first_name: str
    last_name: str
    supervisor_id: Optional[uuid.UUID] = Field(default=None, foreign_key="employee.id")
    birthdate: datetime
    updated_by: Optional[uuid.UUID] = Field(default=None)
    weekly_hours: float
    works_saturday: bool = Field(default=False)
    
    user: Optional["User"] = Relationship(back_populates="employee")
    supervisor: Optional["Employee"] = Relationship(back_populates="subordinates")
    subordinates: list["Employee"] = Relationship(back_populates="supervisor")
    time_entries: list["TimeEntry"] = Relationship(back_populates="employee")
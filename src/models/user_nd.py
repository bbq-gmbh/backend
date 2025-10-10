from sqlmodel import create_engine, Field, Relationship, SQLModel, Session
import os
from pathlib import Path
from dotenv import load_dotenv
import uuid
from datetime import datetime, timezone, time
from enum import Enum
from sqlalchemy import Column, ForeignKey, Enum as SAEnum
from typing import Optional, TYPE_CHECKING



class User(SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    username: str = Field(unique=True, index=True)
    password_hash: str
    token_key: uuid.UUID = Field(default_factory=uuid.uuid4, index=True)
    is_active: bool = Field(default=True)
    is_superuser: bool = Field(default=False)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column_kwargs={"onupdate": lambda: datetime.now(timezone.utc)}
        )
    updated_by: Optional[uuid.UUID] = Field(default=None)

    employee_id: Optional[uuid.UUID] = Field(default=None, foreign_key="employee.id", index=True)
    
    
    employee: Optional["Employee"] = Relationship(back_populates="user")
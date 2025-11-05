import uuid

from datetime import datetime, date
from typing import Optional

from pydantic import BaseModel

from app.models.time_entry import TimeEntryType


class TimeEntryCreate(BaseModel):
    user_id: uuid.UUID

    entry_type: TimeEntryType
    date_time: datetime


class TimeEntryDelete(BaseModel):
    id: int


class TimeEntryGet(BaseModel):
    user_id: uuid.UUID
    id: Optional[int] = None
    date: Optional[date] = None
    from_date: Optional[date] = None
    to_date: Optional[date] = None

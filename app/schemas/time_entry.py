from datetime import datetime
import uuid

from pydantic import BaseModel

from app.models.time_entry import TimeEntryType


class TimeEntryCreate(BaseModel):
    user_id: uuid.UUID
    entry_type: TimeEntryType
    date_time: datetime


class TimeEntryUpdate(BaseModel):
    id: int
    date_time: datetime


class TimeEntryDelete(BaseModel):
    id: int

from datetime import datetime
from enum import Enum
from typing import Optional
import uuid

from pydantic import BaseModel

from app.models.time_entry import TimeEntryType


class TimeEntryViolationLevel(Enum):
    Warning = "warning"
    Severe = "severe"
    Denied = "denied"


class TimeEntryViolation(BaseModel):
    id: str


class TimeEntryViolationReason(TimeEntryViolation):
    level: TimeEntryViolationLevel
    reason: str


class TimeEntryCreate(BaseModel):
    user_id: uuid.UUID

    entry_type: TimeEntryType
    date_time: datetime

    # ignore: Optional[list[TimeEntryViolation]] = None


class TimeEntryDelete(BaseModel):
    id: int

import uuid

from typing import Optional
from datetime import date

from pydantic import BaseModel

from app.models.absence_entry import AbsenceEntryType


class AbsenceEntryCreate(BaseModel):
    user_id: uuid.UUID

    entry_type: AbsenceEntryType
    date_begin: date
    date_end: date


class AbsenceEntryDelete(BaseModel):
    id: int


class AbsenceEntryGet(BaseModel):
    user_id: uuid.UUID

    id: Optional[int]
    date: Optional[date]
    from_date: Optional[date]
    to_date: Optional[date]

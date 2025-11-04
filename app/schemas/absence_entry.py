from datetime import date
from typing import Optional
import uuid

from pydantic import BaseModel

from app.models.absence_entry import AbsenceEntryType


class AbsenceEntryCreate(BaseModel):
    user_id: uuid.UUID

    entry_type: AbsenceEntryType
    date_start: date
    date_end: date

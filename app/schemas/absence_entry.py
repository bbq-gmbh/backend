import uuid

from datetime import date

from pydantic import BaseModel

from app.models.absence_entry import AbsenceEntryType


class AbsenceEntryCreate(BaseModel):
    user_id: uuid.UUID

    entry_type: AbsenceEntryType
    date_begin: date
    date_end: date

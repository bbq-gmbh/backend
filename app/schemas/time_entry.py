import uuid

from pydantic import BaseModel


class TimeEntryCreate(BaseModel):
    user_id: uuid.UUID
    # TODO


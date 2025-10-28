from zoneinfo import ZoneInfo

from sqlmodel import Field, SQLModel
from sqlalchemy.orm import validates


class ServerStore(SQLModel, table=True):
    __tablename__: str = "server_store"
    id: int = Field(default=1, primary_key=True)
    timezone: str

    @validates("timezone")
    def validate_timezone(self, _key, value):
        """Validate timezone and convert ZoneInfo to string."""
        if isinstance(value, ZoneInfo):
            return str(value)
        ZoneInfo(value)
        return value

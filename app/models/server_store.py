from zoneinfo import ZoneInfo

from sqlmodel import Field, SQLModel


class ServerStore(SQLModel, table=True):
    __tablename__: str = "server_store"
    id: int = Field(default=1, primary_key=True)
    timezone: ZoneInfo

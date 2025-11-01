from zoneinfo import ZoneInfo

from pydantic import BaseModel


class ServerStoreCreate(BaseModel):
    timezone: ZoneInfo

from typing import Optional
from zoneinfo import ZoneInfo
from sqlmodel import Session

from app.models.server_store import ServerStore
from app.schemas.server_store import ServerStoreCreate


class ServerStoreRepository:
    def __init__(self, session: Session):
        self.session = session

    def try_get(self) -> Optional[ServerStore]:
        return self.session.get(ServerStore, 1)

    def get(self) -> ServerStore:
        return self.session.get_one(ServerStore, 1)

    def create(self, server_store_in: ServerStoreCreate) -> ServerStore:
        server_store = ServerStore(id=1, timezone=str(server_store_in.timezone))
        self.session.add(server_store)
        return server_store

    def get_timezone(self) -> ZoneInfo:
        return ZoneInfo(self.get().timezone)

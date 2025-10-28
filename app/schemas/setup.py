from pydantic import BaseModel

from .user import UserCreate
from .server_store import ServerStoreCreate


class SetupCreate(BaseModel):
    user: UserCreate
    server_store: ServerStoreCreate
    pass

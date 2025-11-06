from typing import Optional
from fastapi import APIRouter, Query

from app.api.dependencies import CurrentUserDep, ServerStoreRepositoryDep
from app.core.exceptions import UserNotAuthorizedError
from app.models.server_store import ServerStore


router = APIRouter()


@router.get(
    "/",
    name="Get Server Store",
    operation_id="getServerStore",
    response_model=ServerStore,
)
def get_server_store(
    _: CurrentUserDep, server_store_repo: ServerStoreRepositoryDep
) -> ServerStore:
    return server_store_repo.get()


@router.patch(
    "/",
    name="Patch Server Store Gleitzeit Warnungen",
    operation_id="patchServerStoreGleitzeitWarnungen",
    response_model=ServerStore,
)
def patch_server_store_gleitzeit_warnungen(
    user: CurrentUserDep,
    server_store_repo: ServerStoreRepositoryDep,
    gleitzeit_warnung_gelb: Optional[int] = Query(None),
    gleitzeit_warnung_rot: Optional[int] = Query(None),
) -> ServerStore:
    if not user.is_superuser:
        raise UserNotAuthorizedError()
    server_store = server_store_repo.get()
    server_store.gleitzeit_warnung_gelb = gleitzeit_warnung_gelb
    server_store.gleitzeit_warnung_rot = gleitzeit_warnung_rot

    server_store_repo.session.add(server_store)
    server_store_repo.session.commit()

    return server_store

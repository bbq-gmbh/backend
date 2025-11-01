from fastapi import APIRouter, status

from app.api.dependencies import SetupServiceDep
from app.schemas.setup import GetSetupStatus, SetupCreate

router = APIRouter()


@router.get(
    "/",
    name="Get Setup Status",
    operation_id="getSetupStatus",
    status_code=status.HTTP_201_CREATED,
    response_model=GetSetupStatus,
)
def get_setup_status(setup_service: SetupServiceDep):
    return GetSetupStatus(is_setup=setup_service.check_is_setup())


@router.post(
    "/",
    name="Setup Create",
    operation_id="setupCreate",
    status_code=status.HTTP_201_CREATED,
)
def setup_create(setup_service: SetupServiceDep, setup_in: SetupCreate) -> None:
    setup_service.setup_create(setup_in)

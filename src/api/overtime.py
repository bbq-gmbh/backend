from fastapi import APIRouter, status

from src.api.dependencies import CurrentUserDep, TimeRecordServiceDep


router = APIRouter()

@router.post(
    "/time-record",
    status_code=status.HTTP_201_CREATED
)
def create_overtime (user: CurrentUserDep, time_record_service: TimeRecordServiceDep) -> None:
    time_record_service.create_time_record(user=user)
    pass

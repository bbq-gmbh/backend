from typing import Optional
from fastapi import APIRouter, Query, status

from app.api.dependencies import CurrentUserDep, EmployeeServiceDep, TimeEntryServiceDep
from app.models.time_entry import TimeEntry
from app.schemas.time_entry import TimeEntryCreate, TimeEntryDelete, TimeEntryGet


router = APIRouter()


@router.post(
    "/",
    name="Create Time Entry",
    operation_id="createTimeEntry",
    status_code=status.HTTP_201_CREATED,
)
def create_time_entry(
    user: CurrentUserDep,
    time_entry_service: TimeEntryServiceDep,
    time_entry_in: TimeEntryCreate,
    force: bool = Query(False),
) -> TimeEntry:
    """Create a time entry for an employee."""
    return time_entry_service.create_time_entry(
        user, time_entry_in, force=force or False
    )


@router.delete(
    "/",
    name="Delete Time Entry",
    operation_id="deleteTimeEntry",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_time_entry(
    user: CurrentUserDep,
    time_entry_service: TimeEntryServiceDep,
    time_entry_delte: TimeEntryDelete,
    force: Optional[bool] = Query(),
) -> None:
    time_entry_service.delete_time_entry(user, time_entry_delte, force=force or False)


@router.get(
    "/",
    name="Get Time Entries",
    operation_id="getTimeEntries",
    status_code=status.HTTP_200_OK,
)
def get_time_entries(
    user: CurrentUserDep,
    employee_service: EmployeeServiceDep,
    time_entry_service: TimeEntryServiceDep,
    time_entry_get: TimeEntryGet,
) -> Optional[TimeEntry] | list[TimeEntry]:
    """Get time entries for an employee by ID, date, or date range."""
    return time_entry_service.get_time_entries(employee_service, user, time_entry_get)

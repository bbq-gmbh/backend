from typing import Optional
from fastapi import APIRouter, Query, status

from app.api.dependencies import CurrentUserDep, EmployeeServiceDep, TimeEntryServiceDep
from app.models.absence_entry import AbsenceEntry
from app.schemas.absence_entry import (
    AbsenceEntryCreate,
    AbsenceEntryDelete,
    AbsenceEntryGet,
)

router = APIRouter()


@router.post(
    "/",
    name="Create Absence Entry",
    operation_id="createAbsenceEntry",
    status_code=status.HTTP_201_CREATED,
)
def create_absence_entry(
    user: CurrentUserDep,
    time_entry_service: TimeEntryServiceDep,
    absence_entry_in: AbsenceEntryCreate,
    force: bool = Query(False),
    dry: bool = Query(False),
) -> AbsenceEntry:
    """Create an absence entry for an employee."""
    return time_entry_service.create_absence_entry(
        user, absence_entry_in, force=force, dry=dry
    )


@router.delete(
    "/",
    name="Delete Absence Entry",
    operation_id="deleteAbsenceEntry",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_absence_entry(
    user: CurrentUserDep,
    time_entry_service: TimeEntryServiceDep,
    absence_entry_delete: AbsenceEntryDelete,
) -> None:
    time_entry_service.delete_absence_entry(user, absence_entry_delete)


@router.get(
    "/",
    name="Get Absence Entries",
    operation_id="getAbsenceEntries",
    status_code=status.HTTP_200_OK,
)
def get_absence_entries(
    user: CurrentUserDep,
    employee_service: EmployeeServiceDep,
    time_entry_service: TimeEntryServiceDep,
    absence_entry_get: AbsenceEntryGet,
) -> Optional[AbsenceEntry] | list[AbsenceEntry]:
    """Get absence entries for an employee by ID, date, or date range."""
    return time_entry_service.get_absence_entries(
        employee_service, user, absence_entry_get
    )

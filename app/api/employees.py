from typing import Optional
import uuid
from fastapi import APIRouter, HTTPException, Query, status

from app.api.dependencies import CurrentUserDep, EmployeeServiceDep, TimeEntryServiceDep
from app.core.exceptions import (
    EmployeeAlreadyExistsError,
    UserNotAuthorizedError,
    UserNotFoundError,
)
from app.models.employee import Employee
from app.schemas.employee import (
    EmployeeCreate,
    HierarchyResponse,
    HierarchyRebuildResponse,
    HierarchyRebuildStats,
)

router = APIRouter()


@router.get(
    "/me",
    name="Get Current Employee",
    operation_id="getCurrentEmployee",
    status_code=status.HTTP_200_OK,
)
def get_my_employee(user: CurrentUserDep):
    return user.employee


@router.get(
    "/{user_id}/hierarchy",
    name="Get Employee Hierarchy",
    operation_id="getEmployeeHierarchy",
    status_code=status.HTTP_200_OK,
    response_model=HierarchyResponse,
)
def get_employee_hierarchy(
    user: CurrentUserDep, employee_service: EmployeeServiceDep, user_id: uuid.UUID
):
    """Get hierarchy information for an employee including supervisors and subordinates."""
    # Get the target employee
    target_employee = employee_service.get_employee_by_user_id(user_id)
    if not target_employee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Employee not found for user {user_id}",
        )

    # Authorization check
    if not user.is_superuser:
        # Non-superusers can only view their own hierarchy or subordinates
        if user.employee:
            if not employee_service.is_supervisor_of(
                user.employee, target_employee, include_self=True
            ):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Not authorized to view this employee's hierarchy",
                )
        elif user_id != user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to view this employee's hierarchy",
            )

    # Get and return hierarchy
    hierarchy_data = employee_service.get_hierarchy_for_employee(target_employee)
    return HierarchyResponse(**hierarchy_data)


@router.get(
    "/{user_id}",
    name="Get Employee By User ID",
    operation_id="getEmployeeByUserId",
    status_code=status.HTTP_200_OK,
    response_model=Optional[Employee],
)
def get_employee_by_user_id(
    _: CurrentUserDep, user_id: uuid.UUID, employee_service: EmployeeServiceDep
):
    try:
        employee = employee_service.get_employee_by_user_id(user_id=user_id)
        if not employee:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Employee not found for user {user_id}",
            )
        return employee
    except UserNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"User {user_id} not found"
        )


@router.post(
    "/",
    name="Create Employee",
    operation_id="createEmployee",
    status_code=status.HTTP_201_CREATED,
)
def create_employee(
    _: CurrentUserDep, employee_in: EmployeeCreate, employee_service: EmployeeServiceDep
):
    try:
        employee = employee_service.create_employee_for_user(employee_in)
        return employee
    except UserNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except EmployeeAlreadyExistsError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))


@router.delete(
    "/{user_id}",
    name="Delete Employee",
    operation_id="deleteEmployee",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_employee(
    user: CurrentUserDep, user_id: uuid.UUID, employee_service: EmployeeServiceDep
):
    """Delete an employee and heal the hierarchy (superuser only)."""
    if not user.is_superuser:
        raise UserNotAuthorizedError()

    try:
        employee = employee_service.get_employee_by_user_id(user_id)
        if not employee:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Employee not found for user {user_id}",
            )

        employee_service.delete_employee_and_heal_hierarchy(employee)

    except UserNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"User {user_id} not found"
        )


@router.post(
    "/__rebuild_hierarchy",
    name="Rebuild Employee Hierarchy",
    operation_id="rebuildEmployeeHierarchy",
    status_code=status.HTTP_200_OK,
    response_model=HierarchyRebuildResponse,
)
def rebuild_employee_hierarchy(
    user: CurrentUserDep,
    employee_service: EmployeeServiceDep,
    force: bool = Query(
        False, description="Force rebuild without pre-validation checks"
    ),
):
    """Rebuild the entire employee hierarchy table (superuser only)."""
    if not user.is_superuser:
        raise UserNotAuthorizedError()

    result = employee_service.rebuild_hierarchy(force=force)

    if result["success"]:
        return HierarchyRebuildResponse(
            success=True,
            message=result["message"],
            stats=HierarchyRebuildStats(**result["stats"]),
        )
    else:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=result["message"],
        )


# ==================== Time Entry Endpoints ====================


@router.post(
    "/{user_id}/time_entries",
    name="Create Time Entry",
    operation_id="createTimeEntry",
    status_code=status.HTTP_201_CREATED,
)
def create_time_entry(
    user: CurrentUserDep,
    user_id: uuid.UUID,
    employee_service: EmployeeServiceDep,
    time_entry_service: TimeEntryServiceDep,
):
    """Create a time entry for an employee."""
    pass


@router.get(
    "/{user_id}/time_entries",
    name="Get Time Entries",
    operation_id="getTimeEntries",
    status_code=status.HTTP_200_OK,
)
def get_time_entries(
    user: CurrentUserDep,
    user_id: uuid.UUID,
    employee_service: EmployeeServiceDep,
    time_entry_service: TimeEntryServiceDep,
    id: Optional[uuid.UUID] = Query(None, description="Get time entry by ID"),
    date: Optional[str] = Query(None, description="Get time entries at date"),
    from_date: Optional[str] = Query(
        None, alias="from", description="Get time entries from date"
    ),
    to_date: Optional[str] = Query(
        None, alias="to", description="Get time entries to date"
    ),
):
    """Get time entries for an employee by ID, date, or date range."""
    pass


# ==================== Absence Entry Endpoints ====================


@router.post(
    "/{user_id}/absence_entries",
    name="Create Absence Entry",
    operation_id="createAbsenceEntry",
    status_code=status.HTTP_201_CREATED,
)
def create_absence_entry(
    user: CurrentUserDep,
    user_id: uuid.UUID,
    employee_service: EmployeeServiceDep,
    time_entry_service: TimeEntryServiceDep,
    dry: bool = Query(False, description="Dry run without persisting changes"),
):
    """Create an absence entry for an employee."""
    pass


@router.get(
    "/{user_id}/absence_entries",
    name="Get Absence Entries",
    operation_id="getAbsenceEntries",
    status_code=status.HTTP_200_OK,
)
def get_absence_entries(
    user: CurrentUserDep,
    user_id: uuid.UUID,
    employee_service: EmployeeServiceDep,
    time_entry_service: TimeEntryServiceDep,
    id: Optional[uuid.UUID] = Query(None, description="Get absence entry by ID"),
    date: Optional[str] = Query(None, description="Get absence entries at date"),
    from_date: Optional[str] = Query(
        None, alias="from", description="Get absence entries from date"
    ),
    to_date: Optional[str] = Query(
        None, alias="to", description="Get absence entries to date"
    ),
):
    """Get absence entries for an employee by ID, date, or date range."""
    pass

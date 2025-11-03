import uuid
from fastapi import APIRouter, HTTPException, Query, status
from typing import Optional

from app.api.dependencies import CurrentUserDep, EmployeeServiceDep
from app.core.exceptions import (
    EmployeeAlreadyExistsError,
    UserNotAuthorizedError,
    UserNotFoundError,
)
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
    "/hierarchy",
    name="Get Employee Hierarchy",
    operation_id="getEmployeeHierarchy",
    status_code=status.HTTP_200_OK,
    response_model=HierarchyResponse,
)
def get_employee_hierarchy(
    user: CurrentUserDep,
    employee_service: EmployeeServiceDep,
    user_id: Optional[uuid.UUID] = Query(None, description="User ID to get hierarchy for. If not provided, returns current user's hierarchy.")
):
    """
    Get hierarchy information for an employee.
    
    Returns the employee's position in the hierarchy including:
    - Employee information with depth
    - List of all supervisors (direct and indirect)
    - List of all subordinates (direct and indirect)
    
    Superusers can query any employee's hierarchy. 
    Non-superusers can only query their own hierarchy or subordinates.
    """
    # Determine which employee to query
    target_user_id = user_id if user_id else user.id
    
    # Get the target employee
    target_employee = employee_service.get_employee_by_user_id(target_user_id)
    if not target_employee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Employee not found for user {target_user_id}",
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
        elif target_user_id != user.id:
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
    force: bool = Query(False, description="Force rebuild without pre-validation checks"),
):
    """
    Rebuild the entire employee hierarchy table.
    
    ⚠️ SUPERUSER ONLY - This is a critical maintenance operation.
    
    This endpoint:
    1. Clears the entire employee_hierarchy closure table
    2. Rebuilds all hierarchy relationships from supervisor_id references
    3. Validates the rebuilt hierarchy
    4. Returns detailed statistics and validation results
    
    Args:
        force: If true, skip pre-validation checks and force rebuild
        
    Returns:
        Rebuild report with statistics and validation results
        
    Raises:
        403: If user is not a superuser
    """
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

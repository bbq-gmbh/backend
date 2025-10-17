import uuid
from fastapi import APIRouter, status

from app.api.dependencies import CurrentUserDep, EmployeeServiceDep, UserServiceDep
from app.schemas.employee import EmployeeCreateForUser
from app.schemas.user import UserCreate, UserRead

router = APIRouter()


@router.get(
    "/{user_id}",
    name="Get Employees",
    operation_id="getEmployees",
    status_code=status.HTTP_200_OK,
)
def get_employee_by_user_id(
    _: CurrentUserDep,
    user_id: uuid.UUID,
    employee_service: EmployeeServiceDep
):
    """
    Get employee for a specific user.
    """
    # TODO: auth
    return employee_service.get_employee_by_user_id(user_id=user_id)

@router.post(
    "/",
    name="Create Employee",
    operation_id="createEmployee",
    status_code=status.HTTP_201_CREATED,
)
def create_employee(
    _: CurrentUserDep,
    employee_in: EmployeeCreateForUser,
    employee_service: EmployeeServiceDep,
):
    """
    Create a new employee.
    """
    # TODO: auth
    employee_service.create_employee_for_user(employee_in=employee_in)

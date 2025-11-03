import uuid
from fastapi import APIRouter, HTTPException, status

from app.api.dependencies import CurrentUserDep, EmployeeServiceDep
from app.core.exceptions import (
    EmployeeAlreadyExistsError,
    UserNotFoundError,
)
from app.schemas.employee import EmployeeCreate

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

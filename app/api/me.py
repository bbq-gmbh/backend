from fastapi import APIRouter

from app.api.dependencies import CurrentUserDep
from app.schemas.me import Employee, MeUser


router = APIRouter()


@router.get(
    "/",
    name="Me",
    operation_id="me",
    response_model=MeUser,
)
def get_current_user(user: CurrentUserDep):
    if user.employee:
        employee = Employee(
            first_name=user.employee.first_name, last_name=user.employee.last_name
        )
    else:
        employee = None
    return MeUser(
        id=user.id,
        username=user.username,
        is_superuser=user.is_superuser,
        created_at=user.created_at,
        employee=employee,
    )

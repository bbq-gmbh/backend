from typing import Annotated
from fastapi import APIRouter, Query, status

from app.api.dependencies import CurrentUserDep, UserServiceDep
from app.schemas.query import PagedResult
from app.schemas.user import UserCreate, UserEmployeeOnly, UserInfo

router = APIRouter()


@router.post(
    "/",
    name="Create User",
    operation_id="createUser",
    status_code=status.HTTP_201_CREATED,
    response_model=UserInfo,
)
def create_user(user_in: UserCreate, user_service: UserServiceDep):
    """
    Create a new user.
    """
    return user_service.create_user(user_in=user_in)


@router.get(
    "/", name="List Users", operation_id="listUsers", response_model=list[UserInfo]
)
def list_users(
    user: CurrentUserDep,
    user_service: UserServiceDep,
    page: Annotated[int, Query(ge=0)],
    page_size: Annotated[int, Query(gt=1, lt=200)],
):
    """
    Get a list of all users. Requires authentication.
    """
    result = user_service.get_visible_user_employee_pairs(user, page, page_size)
    return PagedResult(
        page=[
            UserInfo(
                id=u.id,
                username=u.username,
                is_superuser=u.is_superuser,
                created_at=u.created_at,
                employee=UserEmployeeOnly(
                    first_name=e.first_name,
                    last_name=e.last_name,
                )
                if e
                else None,
            )
            for u, e in result.page
        ],
        total=result.total,
    )

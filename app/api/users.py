import uuid
from typing import Annotated
from fastapi import APIRouter, Query, status

from app.api.dependencies import CurrentUserDep, UserServiceDep
from app.schemas.query import PagedResult
from app.schemas.user import UserCreate, UserInfo
from app.services.user import UserService

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


@router.get("/", name="List Users", operation_id="listUsers")
def list_users(
    user: CurrentUserDep,
    user_service: UserServiceDep,
    page: Annotated[int, Query(ge=0)],
    page_size: Annotated[int, Query(ge=1, le=200)],
) -> PagedResult[list[UserInfo]]:
    """
    Get a list of all users. Requires authentication.
    """
    result = user_service.get_visible_user_employee_pairs(user, page, page_size)
    return PagedResult(
        page=[
            UserService._user_employee_pair_to_user_info(u, e) for u, e in result.page
        ],
        total=result.total,
    )


@router.get("/{id}", name="Get User", operation_id="getUser")
def get_user(
    user: CurrentUserDep, user_service: UserServiceDep, id: uuid.UUID
) -> UserInfo:
    return UserService._user_to_user_info(user_service.get_visible_user_by_id(user, id))


@router.delete("/{id}", name="Delete User", operation_id="deleteUser")
def delete_user(
    user: CurrentUserDep, user_service: UserServiceDep, id: uuid.UUID
) -> None:
    user_service.delete_user_by_id(user, id)

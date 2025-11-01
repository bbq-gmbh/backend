import uuid
from typing import Annotated
from fastapi import APIRouter, Query, status

from app.api.dependencies import CurrentUserDep, UserRepositoryDep, UserServiceDep
from app.core.exceptions import UserNotAuthorizedError, UserNotFoundError
from app.schemas.query import PagedResult
from app.schemas.user import UserCreate, UserInfo, UserPatch
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


@router.get("/{id}", name="Get User By Id", operation_id="getUserById")
def get_user_by_id(
    user: CurrentUserDep, user_service: UserServiceDep, id: uuid.UUID
) -> UserInfo:
    return UserService._user_to_user_info(user_service.get_visible_user_by_id(user, id))


@router.delete("/{id}", name="Delete User", operation_id="deleteUser")
def delete_user(
    user: CurrentUserDep, user_service: UserServiceDep, id: uuid.UUID
) -> None:
    user_service.delete_user_by_id(user, id)


@router.get("/exists/{id}", name="User Id Exists", operation_id="userIdExists")
def get_user_id_exists(
    user: CurrentUserDep, user_repo: UserRepositoryDep, id: uuid.UUID
):
    if not user.is_superuser:
        raise UserNotAuthorizedError()

    target = user_repo.get_user_by_id(id)
    if not target:
        raise UserNotFoundError(user_id=id)


@router.get(
    "/exists/username/{name}", name="Username Exists", operation_id="usernameExists"
)
def get_username_exists(user: CurrentUserDep, user_repo: UserRepositoryDep, name: str):
    if not user.is_superuser:
        raise UserNotAuthorizedError()

    target = user_repo.get_user_by_username(name)
    if not target:
        raise UserNotFoundError(username=name)


@router.patch(
    "/{id}",
    name="Patch User",
    operation_id="patchUser",
)
def patch_user(
    user: CurrentUserDep, user_service: UserServiceDep, id: uuid.UUID, user_patch: UserPatch
):
    return user_service.patch_user(user, id, user_patch=user_patch)

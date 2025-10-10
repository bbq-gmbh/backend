from fastapi import APIRouter, status

from app.api.dependencies import CurrentUserDep, UserServiceDep
from app.schemas.user import UserCreate, UserRead

router = APIRouter()


@router.post(
    "/",
    name="Create User",
    operation_id="createUser",
    status_code=status.HTTP_201_CREATED,
    response_model=UserRead,
)
def create_user(user_in: UserCreate, user_service: UserServiceDep):
    """
    Create a new user.
    """
    return user_service.create_user(user_in=user_in)


@router.get(
    "/", name="List Users", operation_id="listUsers", response_model=list[UserRead]
)
def list_users(_: CurrentUserDep, user_service: UserServiceDep):
    """
    Get a list of all users. Requires authentication.
    """
    return user_service.get_all_users()

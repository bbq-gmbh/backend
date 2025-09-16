from fastapi import APIRouter, status

from src.api.dependencies import CurrentUserDep, UserServiceDep
from src.schemas.user import UserCreate, UserResponse

router = APIRouter()


@router.post("/", status_code=status.HTTP_201_CREATED, response_model=UserResponse)
def create_user(user_in: UserCreate, user_service: UserServiceDep):
    """
    Create a new user.
    """
    return user_service.create_user(user_in=user_in)


@router.get("/", response_model=list[UserResponse])
def list_users(_: CurrentUserDep, user_service: UserServiceDep):
    """
    Get a list of all users. Requires authentication.
    """
    return user_service.get_all_users()

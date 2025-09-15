from fastapi import APIRouter, status

from src.api.dependencies import UserServiceDep
from src.schemas.user import UserCreate, UserResponse

router = APIRouter()


@router.post("/", status_code=status.HTTP_201_CREATED, response_model=UserResponse)
def create_user(user_in: UserCreate, user_service: UserServiceDep):
    """
    Create a new user.
    """
    return user_service.create_user(user_in=user_in)

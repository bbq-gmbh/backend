from fastapi import APIRouter

from src.api.dependencies import CurrentUserService, DBSession
from src.schemas.user import UserCreate, UserResponse

router = APIRouter()


@router.post("/", response_model=UserResponse)
def create_user(
    *, session: DBSession, user_in: UserCreate, user_service: CurrentUserService
):
    user = user_service.create_user(user_in=user_in)
    return user

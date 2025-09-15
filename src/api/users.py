from fastapi import APIRouter, Depends
from sqlmodel import Session

from src.api.dependencies import get_session, get_user_service
from src.schemas.user import UserCreate, UserResponse
from src.services.user import UserService

router = APIRouter()


@router.post("/", response_model=UserResponse)
def create_user(
    *,
    session: Session = Depends(get_session),
    user_in: UserCreate,
    user_service: UserService = Depends(get_user_service),
):
    user = user_service.create_user(user_in=user_in)
    return user

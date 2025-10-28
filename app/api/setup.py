from fastapi import APIRouter

from app.api.dependencies import BearerTokenDep

router = APIRouter()


@router.post("/")
def setup_create(bearer_token: BearerTokenDep):
    return bearer_token.credentials

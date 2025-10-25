from fastapi import APIRouter

from app.api.dependencies import BearerTokenDep

router = APIRouter()


# TODO


@router.get("/")
def can_setup(bearer_token: BearerTokenDep):
    return bearer_token.credentials

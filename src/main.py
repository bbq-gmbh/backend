from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import JSONResponse

from src.core.exceptions import (
    DomainError,
    InvalidCredentialsError,
    TokenDecodeError,
    UserAlreadyExistsError,
    UserNotFoundError,
)

from src.api import auth, users
from src.config.database import engine
from src.models.user import User


@asynccontextmanager
async def lifespan(app: FastAPI):
    User.metadata.create_all(engine)
    yield


app = FastAPI(lifespan=lifespan)


@app.exception_handler(UserAlreadyExistsError)
async def user_exists_handler(_, exc: UserAlreadyExistsError):
    return JSONResponse(status_code=409, content={"detail": str(exc)})


@app.exception_handler(UserNotFoundError)
async def user_not_found_handler(_, exc: UserNotFoundError):
    return JSONResponse(status_code=404, content={"detail": str(exc)})


@app.exception_handler(InvalidCredentialsError)
async def invalid_credentials_handler(_, exc: InvalidCredentialsError):
    return JSONResponse(status_code=401, content={"detail": str(exc)})


@app.exception_handler(TokenDecodeError)
async def token_decode_handler(_, exc: TokenDecodeError):
    return JSONResponse(
        status_code=401, content={"detail": "Invalid authentication credentials"}
    )


@app.exception_handler(DomainError)
async def generic_domain_error_handler(_, exc: DomainError):
    return JSONResponse(status_code=400, content={"detail": str(exc)})


app.include_router(users.router, prefix="/users", tags=["users"])
app.include_router(auth.router, prefix="/auth", tags=["auth"])


@app.get("/")
async def read_root() -> dict[str, str]:
    return {"message": "Welcome to the User API"}

from fastapi import FastAPI
from fastapi.responses import JSONResponse

from app.core.exceptions import (
    DomainError,
    InvalidCredentialsError,
    TokenDecodeError,
    UserAlreadyExistsError,
    UserNotFoundError,
    ValidationError,
)


def register_exception_handlers(app: FastAPI) -> None:
    """
    Register all exception handlers with the FastAPI application.

    Args:
        app: FastAPI application instance
    """

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

    @app.exception_handler(ValidationError)
    async def validation_error_handler(_, exc: ValidationError):
        return JSONResponse(status_code=422, content={"detail": str(exc)})

    @app.exception_handler(DomainError)
    async def generic_domain_error_handler(_, exc: DomainError):
        return JSONResponse(status_code=400, content={"detail": str(exc)})

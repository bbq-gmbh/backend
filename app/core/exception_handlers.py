from fastapi import FastAPI
from fastapi.responses import JSONResponse

from app.core.exceptions import (
    AuthenticationError,
    DomainError,
    ResourceConflictError,
    ResourceNotFoundError,
    UnprocessableEntityError,
    ValidationError,
)


def register_exception_handlers(app: FastAPI) -> None:
    """
    Register all exception handlers with the FastAPI application.

    Handles exceptions in order from most specific to most general:
    - 401: Authentication errors
    - 404: Resource not found errors
    - 409: Resource conflict errors
    - 422: Unprocessable entity / validation errors
    - 400: Other domain errors (fallback)

    Args:
        app: FastAPI application instance
    """

    # 401 Unauthorized
    @app.exception_handler(AuthenticationError)
    async def authentication_error_handler(_, exc: AuthenticationError):
        return JSONResponse(status_code=401, content={"detail": str(exc)})

    # 404 Not Found
    @app.exception_handler(ResourceNotFoundError)
    async def resource_not_found_handler(_, exc: ResourceNotFoundError):
        return JSONResponse(status_code=404, content={"detail": str(exc)})

    # 409 Conflict
    @app.exception_handler(ResourceConflictError)
    async def resource_conflict_handler(_, exc: ResourceConflictError):
        return JSONResponse(status_code=409, content={"detail": str(exc)})

    # 422 Unprocessable Entity
    @app.exception_handler(UnprocessableEntityError)
    async def unprocessable_entity_handler(_, exc: UnprocessableEntityError):
        return JSONResponse(status_code=422, content={"detail": str(exc)})

    # 422 Validation Error (legacy)
    @app.exception_handler(ValidationError)
    async def validation_error_handler(_, exc: ValidationError):
        return JSONResponse(status_code=422, content={"detail": str(exc)})

    # 400 Bad Request (catch-all for other domain errors)
    @app.exception_handler(DomainError)
    async def generic_domain_error_handler(_, exc: DomainError):
        return JSONResponse(status_code=400, content={"detail": str(exc)})

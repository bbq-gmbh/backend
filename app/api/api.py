from fastapi import FastAPI

from app.api import auth, overtime, users


def register_routes(app: FastAPI) -> None:
    """
    Register all API routers with the FastAPI application.
    
    Args:
        app: FastAPI application instance
    """
    app.include_router(users.router, prefix="/users", tags=["users"])
    app.include_router(auth.router, prefix="/auth", tags=["auth"])
    app.include_router(overtime.router, prefix="/overtime", tags=["overtime"])

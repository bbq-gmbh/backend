from fastapi import FastAPI

from app.api import auth, employees, me, users, setup


def register_routes(app: FastAPI) -> None:
    """
    Register all API routers with the FastAPI application.

    Args:
        app: FastAPI application instance
    """
    app.include_router(me.router, prefix="/me", tags=["me"])
    app.include_router(users.router, prefix="/users", tags=["users"])
    app.include_router(auth.router, prefix="/auth", tags=["auth"])
    app.include_router(employees.router, prefix="/employees", tags=["employees"])
    app.include_router(setup.router, prefix="/__setup", tags=["setup"])

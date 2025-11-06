from fastapi import FastAPI

from app.api import (
    auth,
    employees,
    me,
    server_store,
    users,
    setup,
    time_entries,
    absence_entries,
)


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
    app.include_router(
        time_entries.router, prefix="/time_entries", tags=["time_entries"]
    )
    app.include_router(
        absence_entries.router, prefix="/absence_entries", tags=["absence_entries"]
    )
    app.include_router(setup.router, prefix="/__setup", tags=["setup"])
    app.include_router(
        server_store.router, prefix="/__server_store", tags=["server_store"]
    )

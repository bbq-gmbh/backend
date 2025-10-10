from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.api import register_routes
from app.config.database import init_db
from app.core.exception_handlers import register_exception_handlers


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager for startup and shutdown events."""
    # Startup: Initialize database (create all tables)
    init_db()
    yield
    # Shutdown: Add cleanup logic here if needed


# Initialize FastAPI application
app = FastAPI(
    title="fs-backend",
    description="Minimal FastAPI + SQLModel auth + users service",
    version="0.1.0",
    lifespan=lifespan,
)

# Register exception handlers
register_exception_handlers(app)

# Register API routes
register_routes(app)


@app.get("/", tags=["health"])
async def read_root() -> None:
    return

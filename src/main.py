from contextlib import asynccontextmanager

from fastapi import FastAPI

from src.api import auth, users
from src.config.database import engine
from src.models.user import User


@asynccontextmanager
async def lifespan(app: FastAPI):
    User.metadata.create_all(engine)
    yield


app = FastAPI(lifespan=lifespan)

app.include_router(users.router, prefix="/users", tags=["users"])
app.include_router(auth.router, prefix="/auth", tags=["auth"])


@app.get("/")
async def read_root() -> dict[str, str]:
    return {"message": "Welcome to the User API"}

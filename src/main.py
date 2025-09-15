from fastapi import FastAPI

from src.api import auth, users
from src.config.database import engine
from src.models.user import User

app = FastAPI()

app.include_router(users.router, prefix="/users", tags=["users"])
app.include_router(auth.router, prefix="/auth", tags=["auth"])


@app.on_event("startup")
def on_startup():
    User.metadata.create_all(engine)


@app.get("/")
def read_root():
    return {"message": "Welcome to the User API"}

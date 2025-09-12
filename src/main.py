from typing import Annotated
import uuid

from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel

import jwt

app = FastAPI()

bearer_scheme = HTTPBearer()


class TokenData(BaseModel):
    user_id: str


class User(BaseModel):
    id: str
    username: str
    password_hash: str


class UserCreateResponse(BaseModel):
    user: User
    token: str


class CreateUserRequest(BaseModel):
    username: str
    password_hash: str


# In-memory database
db: dict[str, User] = {}


def with_user_id(
    token: Annotated[HTTPAuthorizationCredentials, Depends(bearer_scheme)],
) -> str:
    try:
        data = TokenData(
            **jwt.decode(token.credentials, key="secret", algorithms=["HS256"])
        )
        return data.user_id
    except jwt.PyJWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid authentication credentialss {e}",
        )


@app.get("/")
def read_root():
    return {"message": "Welcome to the User API"}


@app.post("/users/", response_model=UserCreateResponse)
def create_user(user_request: CreateUserRequest):
    user_id = str(uuid.uuid4())

    user = User(id=user_id, **user_request.model_dump())
    db[user_id] = user

    token = jwt.encode(
        TokenData(user_id=user_id).model_dump(), key="secret", algorithm="HS256"
    )

    return UserCreateResponse(user=user, token=token)


@app.get("/users/{user_id}", response_model=User)
def read_user(user_id: str):
    user = db.get(user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@app.delete("/users/{user_id}", status_code=204)
def delete_user(user_id: str):
    if user_id not in db:
        raise HTTPException(status_code=404, detail="User not found")
    del db[user_id]
    return


@app.get("/users/")
def list_users():
    return list(db.values())


class DoSomethingResponse(BaseModel):
    name: bool
    user: User


@app.get("/users/do_something", response_model=DoSomethingResponse)
def do_something(user_id: Annotated[str, Depends(with_user_id)]):
    return DoSomethingResponse(name=True, user=db[user_id])

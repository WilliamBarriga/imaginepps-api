from fastapi import APIRouter, status, Response, Body, Query
from fastapi.responses import JSONResponse

prouter = APIRouter()

from datetime import datetime
from pydantic import BaseModel, Field


class Users(BaseModel):
    id: int
    username: str
    email: str


users = [
    {"id": 1, "username": "johndoe", "email": "johndoe@mail.com"},
    {"id": 2, "username": "janedoe", "email": "janedoe@mail.com"},
]


@prouter.get("/users", status_code=status.HTTP_200_OK)
def get_users():
    return users


@prouter.post("/users", status_code=status.HTTP_201_CREATED)
def create_user(user: Users = Body(...)):
    users.append(user.dict())
    return JSONResponse(status_code=status.HTTP_201_CREATED, content=user.dict())


@prouter.get("/users/{paquito_id}", status_code=status.HTTP_200_OK)
def get_user(paquito_id: int):
    for user in users:
        if user["id"] == paquito_id:
            return user
    return {"message": "User not found."}


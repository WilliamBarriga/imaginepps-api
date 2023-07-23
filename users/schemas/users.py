from pydantic import BaseModel, Field


class BaseUser(BaseModel):
    id: str  # id
    name: str
    email: str
    updated_at: str


class Group(BaseModel):
    id: int
    name: str


class User(BaseUser):
    group: Group

class UserPatch(BaseModel):
    name: str | None = Field(None, min_length=3, max_length=50)
    email: str | None = Field(None, min_length=3, max_length=50)
    group_id: int | None = Field(None)
from pydantic import BaseModel, Field
from notes.schemas import tags


class User(BaseModel):
    id: str
    name: str


class Like(BaseModel):
    user: User


class Note(BaseModel):
    id: int = Field(None, gt=0)
    title: str = Field(..., min_length=3, max_length=50)
    content: str = Field(..., min_length=3, max_length=1000)
    favorite: bool = Field(False)
    user_id: str = Field(..., min_length=3, max_length=100)
    updated_at: str = Field(..., min_length=3, max_length=100)


class FullNote(Note):
    tags: list[tags.Tag]
    user: User
    total_likes: int
    likes: list[Like]


class CreateNote(BaseModel):
    title: str = Field(..., min_length=3, max_length=50)
    content: str = Field(..., min_length=3, max_length=1000)
    favorite: bool = Field(False)
    tags: list[str] = Field([], min_length=0, max_length=100)


class PatchNote(BaseModel):
    title: str | None = Field(None, min_length=3, max_length=50)
    content: str | None = Field(None, min_length=3, max_length=1000)
    favorite: bool | None = Field(None)
    tags: list[str] | None = Field(None, min_length=0, max_length=100)

from pydantic import BaseModel, Field


class Tag(BaseModel):
    id: int = Field(None, example=1)
    name: str = Field(None, example="tag1")

from typing import Annotated

# FastAPI
from fastapi import APIRouter, Body, Depends, status, Request, Query
from fastapi.responses import JSONResponse
from fastapi.exceptions import HTTPException
from fastapi.encoders import jsonable_encoder

# Common
from imagine.commons import general_get

# auth_interface
from auth.views.auth import get_current_user

# Schemas
from notes.schemas.tags import Tag

# DB
from imagine.db_manager import db, get_rd, RedisManager

router = APIRouter(dependencies=[Depends(get_current_user)])

@router.get("/", response_model=list[Tag], status_code=status.HTTP_200_OK)
def get_tags(
    cache: Annotated[RedisManager, Depends(get_rd)],
    pagination: Annotated[dict, Depends(general_get)],
) -> JSONResponse:
    """Get all tags

    Args:
        request (Request): request

    Returns:
        JSONResponse: tags
    """
    cache_key = f"tags:{pagination['q']}:{pagination['page']}:{pagination['size']}"
    if (cache_data := cache.get(cache_key)) is not None:
        return JSONResponse(cache_data)

    tags = db.execute_sp(
        "imfun_get_tags",
        f"'{pagination['q']}'::varchar" if pagination["q"] else "null::varchar",
        f"{pagination['page']}::int",
        f"{pagination['size']}::int",
    )
    cache.create(cache_key, tags, 5)

    return JSONResponse(status_code=status.HTTP_200_OK, content=jsonable_encoder(tags))

@router.post("/", response_model=Tag, status_code=status.HTTP_201_CREATED)
def create_tag(
    tag: Tag = Body(...),
) -> JSONResponse:
    """Create a new tag

    Args:
        request (Request): request

    Returns:
        JSONResponse: tag
    """
    db.execute_sp(
        "imfun_create_tag",
        f"'{tag.name}'::varchar",
    )

    return JSONResponse(status_code=status.HTTP_201_CREATED, content={})
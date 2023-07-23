from typing import Annotated

# FastAPI
from fastapi import APIRouter, Body, Depends, status, Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import HTTPException
from fastapi.encoders import jsonable_encoder

# Common
from imagine.commons import general_get

# auth_interface
from auth.views.auth import get_current_user

# Schemas
from users.schemas.users import BaseUser, User, UserPatch

# DB
from imagine.db_manager import db, get_rd, RedisManager

router = APIRouter(dependencies=[Depends(get_current_user)])


@router.get("/", status_code=status.HTTP_200_OK, response_model=list[BaseUser])
def get_all_users(
    cache: Annotated[RedisManager, Depends(get_rd)],
    pagination: Annotated[dict, Depends(general_get)],
) -> JSONResponse:
    """Get all users

    Args:
        request (Request): request

    Returns:
        JSONResponse: users
    """
    cache_key = f"users:{pagination['q']}:{pagination['page']}:{pagination['size']}"
    if (cache_data := cache.get(cache_key)) is not None:
        return JSONResponse(cache_data)

    users = db.execute_sp(
        "imfun_get_users",
        f"'{pagination['q']}'::varchar" if pagination["q"] else "null",
        f"{pagination['page']}::int",
        f"{pagination['size']}::int",
    )
    cache.create(cache_key, users, 5)

    return JSONResponse(status_code=status.HTTP_200_OK, content=jsonable_encoder(users))


@router.get("/{user_id}", status_code=status.HTTP_200_OK, response_model=User)
def get_user(
    cache: Annotated[RedisManager, Depends(get_rd)],
    user_id: str,
) -> JSONResponse:
    """Get user

    Args:
        request (Request): request

    Returns:
        JSONResponse: user
    """
    cache_key = f"user:{user_id}"
    if (cache_data := cache.get(cache_key)) is not None:
        return JSONResponse(cache_data)

    user = db.execute_sp("imfun_get_user", f"'{user_id}'::uuid")
    cache.create(cache_key, user, 5)

    return JSONResponse(status_code=status.HTTP_200_OK, content=jsonable_encoder(user))


@router.patch("/{user_id}", status_code=status.HTTP_200_OK, response_model=User)
def update_user(
    cache: Annotated[RedisManager, Depends(get_rd)],
    user_id: str,
    user: UserPatch,
) -> JSONResponse:
    """Update user

    Args:
        request (Request): request

    Returns:
        JSONResponse: user
    """
    cache.delete(f"users:*")
    cache.delete(f"user:{user_id}")

    user = db.execute_sp(
        "imfun_update_user",
        f"'{user_id}'::uuid",
        f"'{user.name}'::varchar" if user.name else "null::varchar",
        f"'{user.email}'::varchar" if user.email else "null::varchar",
        f"'{user.group_id}'::int" if user.group_id else "null::int",
    )

    return JSONResponse(status_code=status.HTTP_200_OK, content=jsonable_encoder(user))

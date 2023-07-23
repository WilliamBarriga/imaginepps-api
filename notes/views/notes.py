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
from notes.schemas.notes import Note, FullNote, User, CreateNote, PatchNote

# DB
from imagine.db_manager import db, get_rd, RedisManager

router = APIRouter(dependencies=[Depends(get_current_user)])


@router.get("/", response_model=list[Note], status_code=status.HTTP_200_OK)
def get_notes(
    cache: Annotated[RedisManager, Depends(get_rd)],
    pagination: Annotated[dict, Depends(general_get)],
    search_name: str | None = Query(None),
    tags: list[str] | None = Query(None),
    favorites: bool | None = Query(None),
) -> JSONResponse:
    """Get all notes

    Args:
        request (Request): request

    Returns:
        JSONResponse: notes
    """
    cache_key = f"notes:{pagination['q']}:{pagination['page']}:{pagination['size']}"
    if (cache_data := cache.get(cache_key)) is not None:
        return JSONResponse(cache_data)

    notes = db.execute_sp(
        "imfun_get_notes",
        f"'{pagination['q']}'::varchar" if pagination["q"] else "null::varchar",
        f"{pagination['page']}::int",
        f"{pagination['size']}::int",
        f"'{search_name}'::varchar" if search_name else "null::varchar",
        f"'{tags}'::varchar[]" if tags else "null::varchar[]",
        f"'{favorites}'::boolean" if favorites else "null::boolean",
    )
    cache.create(cache_key, notes, 5)

    return JSONResponse(status_code=status.HTTP_200_OK, content=jsonable_encoder(notes))


@router.get("/{note_id}", response_model=FullNote, status_code=status.HTTP_200_OK)
def get_note(
    cache: Annotated[RedisManager, Depends(get_rd)],
    note_id: int,
) -> JSONResponse:
    """Get a note

    Args:
        request (Request): request

    Returns:
        JSONResponse: note
    """
    cache_key = f"note:{note_id}"
    if (cache_data := cache.get(cache_key)) is not None:
        return JSONResponse(cache_data)

    note = db.execute_sp("imfun_get_note", f"{note_id}::int")
    cache.create(cache_key, note, 5)

    return JSONResponse(status_code=status.HTTP_200_OK, content=jsonable_encoder(note))


@router.post("/", response_model=Note, status_code=status.HTTP_201_CREATED)
def create_note(
    cache: Annotated[RedisManager, Depends(get_rd)],
    user: User = Depends(get_current_user),
    note: CreateNote = Body(...),
) -> JSONResponse:
    """Create a note

    Args:
        request (Request): request

    Returns:
        JSONResponse: note
    """

    favorite = "true" if note.favorite else "false"
    
    tags = str(note.tags).replace("[", "{").replace("]", "}").replace("'", "")

    note = db.execute_sp(
        "imfun_create_note",
        f"'{note.title}'::varchar",
        f"'{note.content}'::varchar",
        f"'{tags}'::varchar[]",
        f"{favorite}::boolean",
        f"'{user.id}'::uuid",
    )

    cache.delete(f"notes:*")

    return JSONResponse(
        status_code=status.HTTP_201_CREATED, content=jsonable_encoder(note)
    )


@router.patch("/{note_id}", response_model=Note, status_code=status.HTTP_200_OK)
def patch_note(
    cache: Annotated[RedisManager, Depends(get_rd)],
    note_id: int,
    user: User = Depends(get_current_user),
    note: PatchNote = Body(...),
) -> JSONResponse:
    """Patch a note

    Args:
        request (Request): request

    Returns:
        JSONResponse: note
    """

    favorite = "true" if note.favorite else "false"

    tags = str(note.tags).replace("[", "{").replace("]", "}").replace("'", "")


    db.execute_sp(
        "imfun_patch_note",
        f"{note_id}::int",
        f"'{note.title}'::varchar" if note.title else "null::varchar",
        f"'{note.content}'::varchar" if note.content else "null::varchar",
        f"'{tags}'::varchar[]" if note.tags else "null::varchar[]",
        f"{favorite}::boolean" if note.favorite else "null::boolean",
        f"'{user.id}'::uuid",
    )

    cache.delete(f"notes:*")
    cache.delete(f"note:{note_id}")

    return JSONResponse(status_code=status.HTTP_200_OK, content=jsonable_encoder(note))


@router.post("/{note_id}/like", status_code=status.HTTP_200_OK)
def like_note(
    cache: Annotated[RedisManager, Depends(get_rd)],
    note_id: int,
    user: User = Depends(get_current_user),
) -> JSONResponse:
    """Like a note

    Args:
        request (Request): request

    Returns:
        JSONResponse: note
    """

    db.execute_sp(
        "imfun_like_note",
        f"{note_id}::int",
        f"'{user.id}'::uuid",
    )

    cache.delete(f"notes:*")
    cache.delete(f"note:{note_id}")

    return JSONResponse(status_code=status.HTTP_200_OK, content={})

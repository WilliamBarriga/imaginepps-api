from fastapi import APIRouter
from notes.views.notes import router as notes_router
from notes.views.tags import router as tags_router


api_router = APIRouter()

api_router.include_router(notes_router, prefix="/notes", tags=["notes"])
api_router.include_router(tags_router, prefix="/tags", tags=["notes"])

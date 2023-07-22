from fastapi import APIRouter
from auth.views.auth import prouter, router


api_router = APIRouter()

api_router.include_router(prouter, prefix="/auth", tags=["auth"])
api_router.include_router(router, prefix="", tags=["profile"])
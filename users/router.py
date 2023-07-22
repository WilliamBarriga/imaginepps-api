from fastapi import APIRouter
from users.views.users import prouter as users_router


api_router = APIRouter()

api_router.include_router(users_router, prefix="/users", tags=["users"])
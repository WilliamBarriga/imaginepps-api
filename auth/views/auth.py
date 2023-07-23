from typing import Annotated
from jose import JWTError, jwt

from fastapi import APIRouter, Body, Depends, status, Request
from fastapi.responses import JSONResponse
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from fastapi.exceptions import HTTPException

# Schemas
from auth.schemas.auth import AuthUserBase, AuthUserCreate, Token, UserData

# Services
from auth.services.users import authenticate_user, create_user

# constants
from auth.constants import USER_GROUPS

# DB
from imagine.db_manager import db, get_rd, RedisManager

# Env
from decouple import config

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

prouter = APIRouter()


@prouter.get("/me", status_code=status.HTTP_200_OK)
def get_current_user(
    cache: Annotated[RedisManager, Depends(get_rd)],
    token: str = Depends(oauth2_scheme),
) -> UserData:
    """get the current user

    Args:
        token (str, optional): token. Defaults to Depends(oauth2_scheme).

    Returns:
        UserData: user data
    """
    try:
        payload = jwt.decode(token, config("SECRET_KEY"), algorithms=["HS256"])
        email: str = payload.get("email")
        if email is None:
            raise HTTPException(status_code=401, detail="Invalid authentication")
    except JWTError as e:
        raise HTTPException(status_code=401, detail="Invalid authentication")

    if (cache_data := cache.get(f"user_data:{email}")) is not None:
        return UserData(**cache_data)

    user_data = db.execute_sp("imfun_get_user_data", f"'{email}'::varchar")
    cache.create(f"user_data:{email}", user_data, 5)

    return UserData(**user_data)


router = APIRouter(dependencies=[Depends(get_current_user)])


@prouter.post("/signup", status_code=status.HTTP_201_CREATED)
async def signup(user: AuthUserCreate = Body(...)):
    create_user(user, USER_GROUPS["free_user"])
    return JSONResponse(status_code=status.HTTP_201_CREATED, content=None)


@prouter.post("/login", status_code=status.HTTP_200_OK, response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    token = authenticate_user(form_data.username, form_data.password)
    return Token(access_token=token, token_type="bearer")


@prouter.get("/validate", status_code=status.HTTP_200_OK)
def validate_token(request: Request, cache: Annotated[RedisManager, Depends(get_rd)]):
    token = request.headers.get("Authorization")
    if isinstance(token, str) and "bearer" in token.lower():
        token = token.split(" ")[1]
    else:
        raise HTTPException(status_code=401, detail="Invalid authentication")

    data = get_current_user(cache, token)

    return data

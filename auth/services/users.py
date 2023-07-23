from typing import Any, Optional
import re

from datetime import datetime, timedelta

# JWT
from jose import JWTError, jwt

# FastAPI
from fastapi import Depends
from fastapi.exceptions import HTTPException
from fastapi.security import OAuth2PasswordBearer

# Cryptography
from passlib.context import CryptContext

# Schemas
from auth.schemas.auth import AuthUserCreate, AuthUser, UserData, FullUser

# db
from imagine.db_manager import db

# Env
from decouple import config

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")
ACCESS_TOKEN_EXPIRE_MINUTES = config('ACCESS_TOKEN_EXPIRE_MINUTES', cast=int)


def valid_email(email: str) -> bool:
    expresion_regular = r"(?:[a-z0-9!#$%&'*+/=?^_`{|}~-]+(?:\.[a-z0-9!#$%&'*+/=?^_`{|}~-]+)*|\"(?:[\x01-\x08\x0b\x0c\x0e-\x1f\x21\x23-\x5b\x5d-\x7f]|\\[\x01-\x09\x0b\x0c\x0e-\x7f])*\")@(?:(?:[a-z0-9](?:[a-z0-9-]*[a-z0-9])?\.)+[a-z0-9](?:[a-z0-9-]*[a-z0-9])?|\[(?:(?:(2(5[0-5]|[0-4][0-9])|1[0-9][0-9]|[1-9]?[0-9]))\.){3}(?:(2(5[0-5]|[0-4][0-9])|1[0-9][0-9]|[1-9]?[0-9])|[a-z0-9-]*[a-z0-9]:(?:[\x01-\x08\x0b\x0c\x0e-\x1f\x21-\x5a\x53-\x7f]|\\[\x01-\x09\x0b\x0c\x0e-\x7f])+)\])"
    return re.match(expresion_regular, email) is not None


def verify_password(plain_password: str, hashed_password: str) -> None:
    """verify the password

    Args:
        plain_password (str): plain password
        hashed_password (str): hashed password

    Exceptions:
        HTTPException: if the password is not correct
    """

    verify = pwd_context.verify(plain_password, hashed_password)

    if not verify:
        raise HTTPException(status_code=400, detail="Incorrect password")


def create_access_token(
    data: dict[str, Any], expires_delta: timedelta
) -> str:
    """create the access token

    Args:
        data (Dict[str, Any]): data to encode
        expires_delta (Optional[timedelta], optional): expiration time. Defaults to None.

    Returns:
        str: access token
    """
    to_encode = data.copy()
    expire = datetime.utcnow() + expires_delta
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, config("SECRET_KEY"), algorithm="HS256")
    return encoded_jwt


def generate_token(user: AuthUser) -> str:
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    token_data = {
        "id": user.id,
        "email": user.email,
    }
    access_token = create_access_token(
        data=token_data, expires_delta=access_token_expires
    )
    return access_token


def get_password_hash(password: str) -> str:
    """hash the password

    Args:
        password (str): plain password

    Returns:
        str: hashed password
    """
    return pwd_context.hash(password)


def create_user(user: AuthUserCreate, group_id: int) -> int:
    validate_user = db.fetch_one(
        f"select u.id from users u where u.email = '{user.email}'"
    )
    if validate_user:
        raise HTTPException(
            status_code=400, detail="User with this email already exists."
        )

    password = get_password_hash(user.password)

    user_id = db.execute_sp(
        "imfun_signup_user",
        f"$${user.name}$$::varchar",
        f"$${user.email}$$::varchar",
        f"$${password}$$::varchar",
        f"{group_id}::int8",
    )["user_id"]

    user = AuthUser(**user.dict(), id=user_id, group_id=group_id)

    return user_id


def authenticate_user(email: str, password: str) -> str:
    """authenticate the user on login

    Args:
        email (str): email of the user
        password (str): password of the user

    Returns:
        FullUser: user
    """

    if not valid_email(email):
        raise HTTPException(status_code=400, detail="Invalid email")

    user_data = db.execute_sp("imfun_get_user_data", f"'{email}'::varchar")
    user_data = FullUser(**user_data)
    verify_password(password, user_data.password)
    token = generate_token(user_data)
    return token



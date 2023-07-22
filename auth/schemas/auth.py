from pydantic import BaseModel, EmailStr, SecretStr


class AuthUserBase(BaseModel):
    email: EmailStr
    name: str


class AuthUserCreate(AuthUserBase):
    password: str

class AuthUser(AuthUserBase):
    id: int
    group_id: int

class UserGroup(BaseModel):
    id: int
    name: str

class UserData(BaseModel):
    id: int
    name: str
    email: str
    active: bool
    group: UserGroup

class FullUser(UserData):
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str
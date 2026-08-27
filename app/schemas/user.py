from datetime import datetime
from pydantic import BaseModel


class UserCreate(BaseModel):
    username: str
    email: str
    password: str


class UserResponse(BaseModel):
    id: int
    username: str
    display_name: str | None
    email: str
    created_at: datetime


class TokenResponse(BaseModel):
    access_token: str
    token_type: str
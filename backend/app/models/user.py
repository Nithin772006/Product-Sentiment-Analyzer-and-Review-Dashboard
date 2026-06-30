from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional
from pydantic import BaseModel, Field


class User(BaseModel):
    id: Optional[str] = Field(None, alias="_id")
    username: str
    password_hash: str
    role: str = "user"  # "admin" | "user"
    created_at: datetime = Field(default_factory=lambda: datetime.now(tz=timezone.utc))

    class Config:
        populate_by_name = True


class UserRegister(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=6, max_length=100)
    role: Optional[str] = "user"


class UserLogin(BaseModel):
    username: str
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str
    username: str

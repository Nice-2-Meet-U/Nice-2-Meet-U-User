from __future__ import annotations

from datetime import datetime
from typing import Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, EmailStr, Field


class UserPublic(BaseModel):
    """Public representation of a user returned to clients."""

    id: UUID = Field(default_factory=uuid4)
    email: EmailStr
    name: Optional[str] = None
    provider: str
    picture: Optional[str] = None
    last_login: Optional[datetime] = None


class SignupRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)
    name: Optional[str] = None


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    token: str
    user: UserPublic
    profile_id: Optional[UUID] = None

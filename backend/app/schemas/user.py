"""
Pydantic schemas for auth-related requests/responses. These validate
incoming request bodies and shape outgoing responses — kept separate
from models/user.py (the SQLAlchemy table) since the API shape and the
DB shape aren't always identical (e.g., we never return password_hash).
"""

import uuid

from pydantic import BaseModel, EmailStr, Field

from app.models.user import UserRole


class UserRegister(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)
    role: UserRole
    preferred_language: str = "en"


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserOut(BaseModel):
    """Safe, public-facing representation of a user — never includes
    password_hash. Returned after register/login and from /me."""

    id: uuid.UUID
    email: EmailStr
    role: UserRole
    preferred_language: str

    class Config:
        from_attributes = True  # allows creating this directly from an ORM User object


class TokenPair(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshRequest(BaseModel):
    refresh_token: str
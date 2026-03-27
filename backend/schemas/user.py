from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime

from models.user import UserRole


# ─── Base ────────────────────────────────────────────────────────────────────
class UserBase(BaseModel):
    email:     EmailStr
    full_name: str       = Field(..., min_length=2, max_length=255)
    role:      UserRole  = UserRole.EMPLOYEE
    avatar_url: Optional[str] = None


# ─── Create ──────────────────────────────────────────────────────────────────
class UserCreate(UserBase):
    password: str = Field(..., min_length=8, max_length=100)


# ─── Update ──────────────────────────────────────────────────────────────────
class UserUpdate(BaseModel):
    full_name:  Optional[str]      = None
    avatar_url: Optional[str]      = None
    role:       Optional[UserRole] = None
    is_active:  Optional[bool]     = None


# ─── Response ────────────────────────────────────────────────────────────────
class UserResponse(UserBase):
    id:          int
    is_active:   bool
    is_verified: bool
    created_at:  datetime
    last_login:  Optional[datetime] = None

    model_config = {"from_attributes": True}


# ─── Auth schemas ─────────────────────────────────────────────────────────────
class LoginRequest(BaseModel):
    email:    EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type:   str = "bearer"
    user:         UserResponse


class TokenData(BaseModel):
    user_id: Optional[int] = None
    role:    Optional[str] = None

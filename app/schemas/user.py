from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class UserCreate(BaseModel):
    email: str
    password: str = Field(min_length=8)
    full_name: str | None = None

UserRole = Literal["admin", "manager", "member"]

class UserUpdate(BaseModel):
    full_name: str | None = Field(
        default=None,
        max_length=255,
    )
    role: UserRole | None = None
    is_active: bool | None = None


class UserRoleUpdate(BaseModel):
    role: UserRole


class UserStatusUpdate(BaseModel):
    is_active: bool


class UserResponse(BaseModel):
    id: int
    email: str
    full_name: str | None
    role: str
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
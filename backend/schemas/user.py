"""
HealthVault AI — User Schemas
"""
import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field


class UserBase(BaseModel):
    email: EmailStr
    full_name: Optional[str] = None
    avatar_url: Optional[str] = None
    phone: Optional[str] = None
    whatsapp_number: Optional[str] = None
    timezone: str = "UTC"


class UserCreate(UserBase):
    supabase_uid: uuid.UUID


class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    phone: Optional[str] = None
    whatsapp_number: Optional[str] = None
    timezone: Optional[str] = None
    onboarded: Optional[bool] = None


class UserResponse(UserBase):
    id: uuid.UUID
    supabase_uid: uuid.UUID
    role: str
    is_active: bool
    onboarded: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class UserPublic(BaseModel):
    """Slim public view — safe to return in API responses."""
    id: uuid.UUID
    email: EmailStr
    full_name: Optional[str] = None
    avatar_url: Optional[str] = None
    role: str
    onboarded: bool

    model_config = {"from_attributes": True}

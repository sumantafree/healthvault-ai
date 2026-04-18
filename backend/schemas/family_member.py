"""
HealthVault AI — FamilyMember Schemas
"""
import uuid
from datetime import date, datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class FamilyMemberCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    date_of_birth: Optional[date] = None
    gender: Optional[str] = "other"
    blood_type: Optional[str] = "unknown"
    height_cm: Optional[float] = Field(None, gt=0, lt=300)
    weight_kg: Optional[float] = Field(None, gt=0, lt=500)
    allergies: Optional[List[str]] = None
    chronic_conditions: Optional[List[str]] = None
    emergency_contact: Optional[str] = None
    is_primary: bool = False


class FamilyMemberUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    date_of_birth: Optional[date] = None
    gender: Optional[str] = None
    blood_type: Optional[str] = None
    height_cm: Optional[float] = Field(None, gt=0, lt=300)
    weight_kg: Optional[float] = Field(None, gt=0, lt=500)
    allergies: Optional[List[str]] = None
    chronic_conditions: Optional[List[str]] = None
    emergency_contact: Optional[str] = None
    avatar_url: Optional[str] = None


class FamilyMemberResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    name: str
    date_of_birth: Optional[date] = None
    gender: str
    blood_type: str
    height_cm: Optional[float] = None
    weight_kg: Optional[float] = None
    allergies: Optional[List[str]] = None
    chronic_conditions: Optional[List[str]] = None
    emergency_contact: Optional[str] = None
    avatar_url: Optional[str] = None
    is_primary: bool
    age: Optional[int] = None
    bmi: Optional[float] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}

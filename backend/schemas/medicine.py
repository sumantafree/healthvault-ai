"""
HealthVault AI — Medicine Schemas
"""
import uuid
from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel


class MedicineCreate(BaseModel):
    family_member_id: uuid.UUID
    prescription_id: Optional[uuid.UUID] = None
    name: str
    generic_name: Optional[str] = None
    dosage: Optional[str] = None
    form: Optional[str] = None
    frequency: Optional[str] = None
    instructions: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    refill_reminder: bool = False


class MedicineUpdate(BaseModel):
    name: Optional[str] = None
    dosage: Optional[str] = None
    frequency: Optional[str] = None
    instructions: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    is_active: Optional[bool] = None
    refill_reminder: Optional[bool] = None


class MedicineResponse(BaseModel):
    id: uuid.UUID
    family_member_id: uuid.UUID
    prescription_id: Optional[uuid.UUID] = None
    name: str
    generic_name: Optional[str] = None
    dosage: Optional[str] = None
    form: Optional[str] = None
    frequency: Optional[str] = None
    instructions: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    is_active: bool
    refill_reminder: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}

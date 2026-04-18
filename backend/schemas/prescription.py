"""
HealthVault AI — Prescription Schemas
"""
import uuid
from datetime import date, datetime
from typing import Any, Dict, Optional

from pydantic import BaseModel


class PrescriptionCreate(BaseModel):
    family_member_id: uuid.UUID
    doctor_name: Optional[str] = None
    hospital_name: Optional[str] = None
    prescribed_date: Optional[date] = None
    valid_until: Optional[date] = None
    notes: Optional[str] = None


class PrescriptionResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    family_member_id: uuid.UUID
    file_url: str
    file_name: str
    doctor_name: Optional[str] = None
    hospital_name: Optional[str] = None
    prescribed_date: Optional[date] = None
    valid_until: Optional[date] = None
    parsed_data: Optional[Dict[str, Any]] = None
    notes: Optional[str] = None
    processing_status: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}

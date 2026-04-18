"""
HealthVault AI — HealthReport Schemas
"""
import uuid
from datetime import date, datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel


class HealthReportCreate(BaseModel):
    family_member_id: uuid.UUID
    report_type: str = "other"
    report_date: Optional[date] = None
    lab_name: Optional[str] = None
    doctor_name: Optional[str] = None


class HealthReportResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    family_member_id: uuid.UUID
    file_url: str
    file_name: str
    file_size_bytes: Optional[int] = None
    mime_type: Optional[str] = None
    report_type: str
    report_date: Optional[date] = None
    lab_name: Optional[str] = None
    doctor_name: Optional[str] = None
    ai_summary: Optional[str] = None
    risk_level: str
    processing_status: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class HealthReportDetail(HealthReportResponse):
    """Full report including parsed data — used in detail view."""
    raw_text: Optional[str] = None
    parsed_data: Optional[Dict[str, Any]] = None


class HealthReportList(BaseModel):
    items: List[HealthReportResponse]
    total: int
    page: int
    per_page: int

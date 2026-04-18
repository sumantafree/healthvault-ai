"""
HealthVault AI — HealthMetric Schemas
"""
import uuid
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel


class HealthMetricCreate(BaseModel):
    family_member_id: uuid.UUID
    report_id: Optional[uuid.UUID] = None
    test_name: str
    value: float
    unit: Optional[str] = None
    normal_range_min: Optional[float] = None
    normal_range_max: Optional[float] = None
    normal_range_text: Optional[str] = None
    status: str = "normal"
    category: Optional[str] = None
    measured_at: datetime
    notes: Optional[str] = None


class HealthMetricResponse(BaseModel):
    id: uuid.UUID
    family_member_id: uuid.UUID
    report_id: Optional[uuid.UUID] = None
    test_name: str
    value: float
    unit: Optional[str] = None
    normal_range_min: Optional[float] = None
    normal_range_max: Optional[float] = None
    normal_range_text: Optional[str] = None
    status: str
    category: Optional[str] = None
    measured_at: datetime
    notes: Optional[str] = None
    is_abnormal: bool = False
    created_at: datetime

    model_config = {"from_attributes": True}


class MetricTrendPoint(BaseModel):
    measured_at: datetime
    value: float
    status: str


class MetricTrend(BaseModel):
    test_name: str
    unit: Optional[str]
    normal_range_min: Optional[float]
    normal_range_max: Optional[float]
    data_points: List[MetricTrendPoint]

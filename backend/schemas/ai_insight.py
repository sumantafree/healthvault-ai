"""
HealthVault AI — AIInsight Schemas
"""
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel


class AIInsightResponse(BaseModel):
    id: uuid.UUID
    family_member_id: uuid.UUID
    report_id: Optional[uuid.UUID] = None
    summary: str
    risk_level: str
    risk_factors: Optional[List[str]] = None
    recommendations: Optional[Dict[str, Any]] = None
    disclaimer: str
    model_used: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}

"""
HealthVault AI — Reminder Schemas
"""
import uuid
from datetime import datetime, time
from typing import Optional

from pydantic import BaseModel


class ReminderCreate(BaseModel):
    family_member_id: uuid.UUID
    medicine_id: Optional[uuid.UUID] = None
    title: str
    message: Optional[str] = None
    reminder_time: time
    frequency: str = "daily"
    custom_cron: Optional[str] = None
    whatsapp_number: Optional[str] = None


class ReminderUpdate(BaseModel):
    title: Optional[str] = None
    message: Optional[str] = None
    reminder_time: Optional[time] = None
    frequency: Optional[str] = None
    whatsapp_number: Optional[str] = None
    is_active: Optional[bool] = None


class ReminderResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    family_member_id: uuid.UUID
    medicine_id: Optional[uuid.UUID] = None
    title: str
    message: Optional[str] = None
    reminder_time: time
    frequency: str
    whatsapp_number: Optional[str] = None
    is_active: bool
    last_sent_at: Optional[datetime] = None
    next_send_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}

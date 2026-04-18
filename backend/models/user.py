"""
HealthVault AI — User Model
Mirrors Supabase auth.users with app-specific extensions.
"""
import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    supabase_uid: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), unique=True, nullable=False, index=True
    )
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    full_name: Mapped[str | None] = mapped_column(String(255))
    avatar_url: Mapped[str | None] = mapped_column(Text)
    phone: Mapped[str | None] = mapped_column(String(20))
    role: Mapped[str] = mapped_column(String(20), default="owner")
    whatsapp_number: Mapped[str | None] = mapped_column(String(20))
    timezone: Mapped[str] = mapped_column(String(50), default="UTC")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    onboarded: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    family_members = relationship(
        "FamilyMember", back_populates="user", cascade="all, delete-orphan"
    )
    health_reports = relationship(
        "HealthReport", back_populates="user", cascade="all, delete-orphan"
    )
    prescriptions = relationship(
        "Prescription", back_populates="user", cascade="all, delete-orphan"
    )
    reminders = relationship(
        "Reminder", back_populates="user", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<User id={self.id} email={self.email}>"

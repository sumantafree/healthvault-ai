"""
HealthVault AI — FamilyMember Model
"""
import uuid
from datetime import date, datetime

from sqlalchemy import Boolean, Date, DateTime, Numeric, String, Text, func
from sqlalchemy.dialects.postgresql import ARRAY, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database import Base


class FamilyMember(Base):
    __tablename__ = "family_members"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    date_of_birth: Mapped[date | None] = mapped_column(Date)
    gender: Mapped[str] = mapped_column(String(10), default="other")
    blood_type: Mapped[str] = mapped_column(String(10), default="unknown")
    height_cm: Mapped[float | None] = mapped_column(Numeric(5, 2))
    weight_kg: Mapped[float | None] = mapped_column(Numeric(5, 2))
    allergies: Mapped[list[str] | None] = mapped_column(ARRAY(Text))
    chronic_conditions: Mapped[list[str] | None] = mapped_column(ARRAY(Text))
    emergency_contact: Mapped[str | None] = mapped_column(String(255))
    avatar_url: Mapped[str | None] = mapped_column(Text)
    is_primary: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    user = relationship("User", back_populates="family_members")
    health_reports = relationship(
        "HealthReport", back_populates="family_member", cascade="all, delete-orphan"
    )
    health_metrics = relationship(
        "HealthMetric", back_populates="family_member", cascade="all, delete-orphan"
    )
    ai_insights = relationship(
        "AIInsight", back_populates="family_member", cascade="all, delete-orphan"
    )
    prescriptions = relationship(
        "Prescription", back_populates="family_member", cascade="all, delete-orphan"
    )
    medicines = relationship(
        "Medicine", back_populates="family_member", cascade="all, delete-orphan"
    )
    reminders = relationship(
        "Reminder", back_populates="family_member", cascade="all, delete-orphan"
    )

    @property
    def age(self) -> int | None:
        if not self.date_of_birth:
            return None
        today = date.today()
        return (
            today.year
            - self.date_of_birth.year
            - ((today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day))
        )

    @property
    def bmi(self) -> float | None:
        if self.height_cm and self.weight_kg and self.height_cm > 0:
            return round(self.weight_kg / ((self.height_cm / 100) ** 2), 1)
        return None

    def __repr__(self) -> str:
        return f"<FamilyMember id={self.id} name={self.name}>"

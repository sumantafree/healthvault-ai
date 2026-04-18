"""
HealthVault AI — HealthReport Model
"""
import uuid
from datetime import date, datetime

from sqlalchemy import BigInteger, Date, DateTime, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database import Base


class HealthReport(Base):
    __tablename__ = "health_reports"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    family_member_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    file_url: Mapped[str] = mapped_column(Text, nullable=False)
    file_name: Mapped[str] = mapped_column(String(255), nullable=False)
    file_size_bytes: Mapped[int | None] = mapped_column(BigInteger)
    mime_type: Mapped[str | None] = mapped_column(String(100))
    report_type: Mapped[str] = mapped_column(String(50), default="other")
    report_date: Mapped[date | None] = mapped_column(Date, index=True)
    lab_name: Mapped[str | None] = mapped_column(String(255))
    doctor_name: Mapped[str | None] = mapped_column(String(255))
    raw_text: Mapped[str | None] = mapped_column(Text)
    parsed_data: Mapped[dict | None] = mapped_column(JSONB)
    ai_summary: Mapped[str | None] = mapped_column(Text)
    risk_level: Mapped[str] = mapped_column(String(20), default="low")
    processing_status: Mapped[str] = mapped_column(String(50), default="pending")
    processing_error: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    user = relationship("User", back_populates="health_reports")
    family_member = relationship("FamilyMember", back_populates="health_reports")
    health_metrics = relationship(
        "HealthMetric", back_populates="report", cascade="all, delete-orphan"
    )
    ai_insights = relationship(
        "AIInsight", back_populates="report", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<HealthReport id={self.id} type={self.report_type} status={self.processing_status}>"

"""
HealthVault AI — HealthMetric Model
Individual structured data points extracted from reports.
"""
import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Numeric, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database import Base


class HealthMetric(Base):
    __tablename__ = "health_metrics"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    family_member_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("family_members.id", ondelete="CASCADE"), nullable=False, index=True)
    report_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("health_reports.id", ondelete="SET NULL"), index=True)
    test_name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    value: Mapped[float] = mapped_column(Numeric(12, 4), nullable=False)
    unit: Mapped[str | None] = mapped_column(String(50))
    normal_range_min: Mapped[float | None] = mapped_column(Numeric(12, 4))
    normal_range_max: Mapped[float | None] = mapped_column(Numeric(12, 4))
    normal_range_text: Mapped[str | None] = mapped_column(String(100))
    status: Mapped[str] = mapped_column(String(30), default="normal", index=True)
    category: Mapped[str | None] = mapped_column(String(100))
    measured_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    notes: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    family_member = relationship("FamilyMember", back_populates="health_metrics")
    report = relationship("HealthReport", back_populates="health_metrics")

    @property
    def is_abnormal(self) -> bool:
        return self.status in ("abnormal_low", "abnormal_high")

    def __repr__(self) -> str:
        return f"<HealthMetric {self.test_name}={self.value}{self.unit} ({self.status})>"

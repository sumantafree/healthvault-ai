"""
HealthVault AI — AIInsight Model
LLM-generated health analysis attached to a report.
"""
import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database import Base

DISCLAIMER = (
    "This analysis is for informational purposes only and does not constitute "
    "medical advice. Please consult a qualified healthcare professional for "
    "diagnosis and treatment."
)


class AIInsight(Base):
    __tablename__ = "ai_insights"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    family_member_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("family_members.id", ondelete="CASCADE"), nullable=False, index=True)
    report_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("health_reports.id", ondelete="SET NULL"), index=True)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    risk_level: Mapped[str] = mapped_column(String(20), default="low", index=True)
    risk_factors: Mapped[list[str] | None] = mapped_column(ARRAY(Text))
    recommendations: Mapped[dict | None] = mapped_column(JSONB)
    disclaimer: Mapped[str] = mapped_column(Text, default=DISCLAIMER)
    model_used: Mapped[str | None] = mapped_column(String(100))
    prompt_version: Mapped[str | None] = mapped_column(String(20))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    family_member = relationship("FamilyMember", back_populates="ai_insights")
    report = relationship("HealthReport", back_populates="ai_insights")

    def __repr__(self) -> str:
        return f"<AIInsight id={self.id} risk={self.risk_level}>"

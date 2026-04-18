"""
HealthVault AI — AI Insights Routes
Retrieve AI-generated health summaries and trigger re-analysis.
"""
import uuid
from typing import List, Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from middleware.auth import CurrentUser
from models.ai_insight import AIInsight
from models.family_member import FamilyMember
from models.health_report import HealthReport
from schemas.ai_insight import AIInsightResponse

router = APIRouter(prefix="/insights", tags=["AI Insights"])


# ── Helpers ────────────────────────────────────────────────────────────────────

async def _verify_member_ownership(
    member_id: uuid.UUID,
    user_id: uuid.UUID,
    db: AsyncSession,
) -> FamilyMember:
    result = await db.execute(
        select(FamilyMember).where(
            FamilyMember.id == member_id,
            FamilyMember.user_id == user_id,
        )
    )
    member = result.scalar_one_or_none()
    if not member:
        raise HTTPException(status_code=404, detail="Family member not found.")
    return member


# ── Routes ────────────────────────────────────────────────────────────────────

@router.get(
    "/",
    response_model=List[AIInsightResponse],
    summary="List AI insights for a family member",
)
async def list_insights(
    family_member_id: uuid.UUID,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    limit: int = Query(20, le=100),
) -> List[AIInsight]:
    await _verify_member_ownership(family_member_id, current_user.id, db)

    result = await db.execute(
        select(AIInsight)
        .where(AIInsight.family_member_id == family_member_id)
        .order_by(AIInsight.created_at.desc())
        .limit(limit)
    )
    return result.scalars().all()


@router.get(
    "/latest",
    response_model=AIInsightResponse,
    summary="Get the most recent AI insight for a family member",
)
async def get_latest_insight(
    family_member_id: uuid.UUID,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
) -> AIInsight:
    await _verify_member_ownership(family_member_id, current_user.id, db)

    result = await db.execute(
        select(AIInsight)
        .where(AIInsight.family_member_id == family_member_id)
        .order_by(AIInsight.created_at.desc())
        .limit(1)
    )
    insight = result.scalar_one_or_none()
    if not insight:
        raise HTTPException(
            status_code=404,
            detail="No AI insights found. Upload a health report first.",
        )
    return insight


@router.get(
    "/report/{report_id}",
    response_model=AIInsightResponse,
    summary="Get AI insight for a specific report",
)
async def get_insight_for_report(
    report_id: uuid.UUID,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
) -> AIInsight:
    # Verify the report belongs to this user
    report_result = await db.execute(
        select(HealthReport).where(
            HealthReport.id == report_id,
            HealthReport.user_id == current_user.id,
        )
    )
    if not report_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Report not found.")

    result = await db.execute(
        select(AIInsight)
        .where(AIInsight.report_id == report_id)
        .order_by(AIInsight.created_at.desc())
        .limit(1)
    )
    insight = result.scalar_one_or_none()
    if not insight:
        raise HTTPException(
            status_code=404,
            detail="AI analysis not yet available. Check report processing status.",
        )
    return insight


@router.post(
    "/reanalyze/{report_id}",
    response_model=dict,
    status_code=202,
    summary="Re-trigger AI analysis for a report",
)
async def reanalyze_report(
    report_id: uuid.UUID,
    background_tasks: BackgroundTasks,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    Re-runs the full OCR + LLM pipeline on an already-uploaded report.
    Useful when AI models improve or previous processing failed.
    Returns 202 Accepted immediately.
    """
    result = await db.execute(
        select(HealthReport).where(
            HealthReport.id == report_id,
            HealthReport.user_id == current_user.id,
        )
    )
    report = result.scalar_one_or_none()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found.")

    # Reset status for re-processing
    report.processing_status = "pending"
    report.processing_error = None
    db.add(report)
    await db.commit()

    from ai.pipeline import process_report_pipeline
    background_tasks.add_task(process_report_pipeline, report_id)

    return {
        "message": "Re-analysis started.",
        "report_id": str(report_id),
        "status": "pending",
    }


@router.get(
    "/{insight_id}",
    response_model=AIInsightResponse,
    summary="Get a specific AI insight by ID",
)
async def get_insight(
    insight_id: uuid.UUID,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
) -> AIInsight:
    result = await db.execute(
        select(AIInsight)
        .join(FamilyMember, FamilyMember.id == AIInsight.family_member_id)
        .where(
            AIInsight.id == insight_id,
            FamilyMember.user_id == current_user.id,
        )
    )
    insight = result.scalar_one_or_none()
    if not insight:
        raise HTTPException(status_code=404, detail="Insight not found.")
    return insight

"""
HealthVault AI — Health Report Routes
Upload, retrieve, and manage health reports.
AI parsing is triggered asynchronously after upload.
"""
import uuid
from typing import List, Optional

from fastapi import APIRouter, BackgroundTasks, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from config import settings
from database import get_db
from middleware.auth import CurrentUser
from models.family_member import FamilyMember
from models.health_report import HealthReport
from schemas.health_report import HealthReportDetail, HealthReportList, HealthReportResponse
from utils.file_upload import upload_file_to_supabase, validate_upload

router = APIRouter(prefix="/reports", tags=["Health Reports"])


# ── Background task — Sprint 2 full AI pipeline ───────────────────────────────

async def _trigger_ai_parsing(report_id: uuid.UUID) -> None:
    """Kick off the full OCR → LLM → Insights pipeline."""
    from ai.pipeline import process_report_pipeline
    await process_report_pipeline(report_id)


# ── Routes ────────────────────────────────────────────────────────────────────

@router.post(
    "/",
    response_model=HealthReportResponse,
    status_code=201,
    summary="Upload a health report",
)
async def upload_report(
    background_tasks: BackgroundTasks,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    file: UploadFile = File(..., description="PDF or image of the health report"),
    family_member_id: uuid.UUID = Form(...),
    report_type: str = Form("other"),
    report_date: Optional[str] = Form(None),
    lab_name: Optional[str] = Form(None),
    doctor_name: Optional[str] = Form(None),
) -> HealthReport:
    # Verify family member belongs to current user
    result = await db.execute(
        select(FamilyMember).where(
            FamilyMember.id == family_member_id,
            FamilyMember.user_id == current_user.id,
        )
    )
    if not result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Family member not found.",
        )

    # Validate and read file
    contents = await validate_upload(file)

    # Upload to Supabase Storage
    file_url = await upload_file_to_supabase(
        contents=contents,
        original_filename=file.filename or "report",
        bucket=settings.SUPABASE_BUCKET_REPORTS,
        user_id=current_user.id,
        folder="reports",
    )

    # Create DB record
    report = HealthReport(
        user_id=current_user.id,
        family_member_id=family_member_id,
        file_url=file_url,
        file_name=file.filename or "report",
        file_size_bytes=len(contents),
        mime_type=file.content_type,
        report_type=report_type,
        lab_name=lab_name,
        doctor_name=doctor_name,
        processing_status="pending",
    )

    if report_date:
        from datetime import date
        try:
            report.report_date = date.fromisoformat(report_date)
        except ValueError:
            pass

    db.add(report)
    await db.commit()
    await db.refresh(report)

    # Kick off AI parsing in the background
    background_tasks.add_task(_trigger_ai_parsing, report.id)

    return report


@router.get("/", response_model=HealthReportList, summary="List reports for a family member")
async def list_reports(
    family_member_id: uuid.UUID,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    page: int = 1,
    per_page: int = 20,
) -> HealthReportList:
    # Verify ownership
    fm_result = await db.execute(
        select(FamilyMember).where(
            FamilyMember.id == family_member_id,
            FamilyMember.user_id == current_user.id,
        )
    )
    if not fm_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Family member not found.")

    # Count
    from sqlalchemy import func
    count_result = await db.execute(
        select(func.count()).select_from(HealthReport).where(
            HealthReport.family_member_id == family_member_id
        )
    )
    total = count_result.scalar_one()

    # Paginated fetch
    offset = (page - 1) * per_page
    result = await db.execute(
        select(HealthReport)
        .where(HealthReport.family_member_id == family_member_id)
        .order_by(HealthReport.report_date.desc().nullslast(), HealthReport.created_at.desc())
        .limit(per_page)
        .offset(offset)
    )
    items = result.scalars().all()

    return HealthReportList(items=items, total=total, page=page, per_page=per_page)


@router.get("/{report_id}", response_model=HealthReportDetail, summary="Get report details")
async def get_report(
    report_id: uuid.UUID,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
) -> HealthReport:
    result = await db.execute(
        select(HealthReport).where(
            HealthReport.id == report_id,
            HealthReport.user_id == current_user.id,
        )
    )
    report = result.scalar_one_or_none()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found.")
    return report


@router.delete("/{report_id}", status_code=204, summary="Delete a health report")
async def delete_report(
    report_id: uuid.UUID,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
) -> None:
    result = await db.execute(
        select(HealthReport).where(
            HealthReport.id == report_id,
            HealthReport.user_id == current_user.id,
        )
    )
    report = result.scalar_one_or_none()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found.")
    await db.delete(report)
    await db.commit()

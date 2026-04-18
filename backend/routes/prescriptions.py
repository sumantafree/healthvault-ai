"""
HealthVault AI — Prescription Routes
Upload prescriptions, trigger AI medicine extraction, manage prescription records.

Flow:
  POST /prescriptions/  → validate file → upload to storage → save DB record
                        → background: OCR + LLM extraction → save medicines → update status
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
from models.medicine import Medicine
from models.prescription import Prescription
from schemas.prescription import PrescriptionCreate, PrescriptionResponse
from utils.file_upload import upload_file_to_supabase, validate_upload

router = APIRouter(prefix="/prescriptions", tags=["Prescriptions"])


# ── Background task ────────────────────────────────────────────────────────────

async def _process_prescription(prescription_id: uuid.UUID, contents: bytes, mime_type: str) -> None:
    """
    Background task: OCR + LLM extraction → save medicines → mark done.
    """
    from datetime import date, timedelta
    from database import get_db_context
    from ai.prescription_parser import parse_prescription_file

    async with get_db_context() as db:
        result = await db.execute(select(Prescription).where(Prescription.id == prescription_id))
        prescription = result.scalar_one_or_none()
        if not prescription:
            return

        try:
            prescription.processing_status = "processing"
            db.add(prescription)
            await db.commit()

            # OCR + LLM
            raw_text, parsed = await parse_prescription_file(contents, mime_type)

            # Update prescription metadata from parsed data
            if parsed.doctor_name and not prescription.doctor_name:
                prescription.doctor_name = parsed.doctor_name[:255]
            if parsed.hospital_name and not prescription.hospital_name:
                prescription.hospital_name = parsed.hospital_name[:255]
            if parsed.prescribed_date_as_date and not prescription.prescribed_date:
                prescription.prescribed_date = parsed.prescribed_date_as_date
            if parsed.valid_until_as_date and not prescription.valid_until:
                prescription.valid_until = parsed.valid_until_as_date

            prescription.parsed_data = {
                "medicines": [m.model_dump() for m in parsed.medicines],
                "medicine_count": len(parsed.medicines),
                "prompt_version": parsed.prompt_version,
            }

            # Save extracted medicines
            today = date.today()
            for med in parsed.medicines:
                end_date = (today + timedelta(days=med.duration_days)) if med.duration_days else None
                medicine = Medicine(
                    family_member_id=prescription.family_member_id,
                    prescription_id=prescription.id,
                    name=med.name,
                    generic_name=med.generic_name,
                    dosage=med.dosage,
                    form=med.form,
                    frequency=med.frequency,
                    instructions=med.instructions,
                    start_date=today,
                    end_date=end_date,
                    is_active=True,
                )
                db.add(medicine)

            prescription.processing_status = "done"
            db.add(prescription)
            await db.commit()

        except Exception as exc:
            import logging
            logging.getLogger(__name__).error(
                "prescription_processing_failed",
                prescription_id=str(prescription_id),
                error=str(exc),
                exc_info=True,
            )
            prescription.processing_status = "failed"
            db.add(prescription)
            await db.commit()


# ── Routes ────────────────────────────────────────────────────────────────────

@router.post(
    "/",
    response_model=PrescriptionResponse,
    status_code=201,
    summary="Upload a prescription",
)
async def upload_prescription(
    background_tasks: BackgroundTasks,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    file: UploadFile = File(..., description="PDF or image of the prescription"),
    family_member_id: uuid.UUID = Form(...),
    doctor_name: Optional[str] = Form(None),
    hospital_name: Optional[str] = Form(None),
    prescribed_date: Optional[str] = Form(None),
    notes: Optional[str] = Form(None),
) -> Prescription:
    # Verify family member ownership
    fm_result = await db.execute(
        select(FamilyMember).where(
            FamilyMember.id == family_member_id,
            FamilyMember.user_id == current_user.id,
        )
    )
    if not fm_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Family member not found.")

    # Validate + read file (reuse Sprint 1/2 utility)
    contents = await validate_upload(file)

    # Upload to Supabase Storage
    file_url = await upload_file_to_supabase(
        contents=contents,
        original_filename=file.filename or "prescription",
        bucket=settings.SUPABASE_BUCKET_PRESCRIPTIONS,
        user_id=current_user.id,
        folder="prescriptions",
    )

    prescription = Prescription(
        user_id=current_user.id,
        family_member_id=family_member_id,
        file_url=file_url,
        file_name=file.filename or "prescription",
        doctor_name=doctor_name,
        hospital_name=hospital_name,
        notes=notes,
        processing_status="pending",
    )

    if prescribed_date:
        from datetime import date
        try:
            prescription.prescribed_date = date.fromisoformat(prescribed_date)
        except ValueError:
            pass

    db.add(prescription)
    await db.commit()
    await db.refresh(prescription)

    # Pass contents to background task (avoids re-downloading from storage)
    mime = file.content_type or "application/pdf"
    background_tasks.add_task(_process_prescription, prescription.id, contents, mime)

    return prescription


@router.get(
    "/",
    response_model=List[PrescriptionResponse],
    summary="List prescriptions for a family member",
)
async def list_prescriptions(
    family_member_id: uuid.UUID,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
) -> List[Prescription]:
    fm_result = await db.execute(
        select(FamilyMember).where(
            FamilyMember.id == family_member_id,
            FamilyMember.user_id == current_user.id,
        )
    )
    if not fm_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Family member not found.")

    result = await db.execute(
        select(Prescription)
        .where(Prescription.family_member_id == family_member_id)
        .order_by(Prescription.prescribed_date.desc().nullslast(), Prescription.created_at.desc())
    )
    return result.scalars().all()


@router.get(
    "/{prescription_id}",
    response_model=PrescriptionResponse,
    summary="Get prescription details",
)
async def get_prescription(
    prescription_id: uuid.UUID,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
) -> Prescription:
    result = await db.execute(
        select(Prescription).where(
            Prescription.id == prescription_id,
            Prescription.user_id == current_user.id,
        )
    )
    prescription = result.scalar_one_or_none()
    if not prescription:
        raise HTTPException(status_code=404, detail="Prescription not found.")
    return prescription


@router.post(
    "/{prescription_id}/reprocess",
    response_model=dict,
    status_code=202,
    summary="Re-trigger AI extraction for a prescription",
)
async def reprocess_prescription(
    prescription_id: uuid.UUID,
    background_tasks: BackgroundTasks,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
) -> dict:
    result = await db.execute(
        select(Prescription).where(
            Prescription.id == prescription_id,
            Prescription.user_id == current_user.id,
        )
    )
    prescription = result.scalar_one_or_none()
    if not prescription:
        raise HTTPException(status_code=404, detail="Prescription not found.")

    import httpx
    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.get(prescription.file_url)
        resp.raise_for_status()
    contents = resp.content
    mime = prescription.file_name.rsplit(".", 1)[-1].lower()
    mime_map = {"pdf": "application/pdf", "jpg": "image/jpeg", "jpeg": "image/jpeg", "png": "image/png"}
    mime_type = mime_map.get(mime, "application/pdf")

    prescription.processing_status = "pending"
    prescription.processing_error = None
    db.add(prescription)
    await db.commit()

    background_tasks.add_task(_process_prescription, prescription_id, contents, mime_type)
    return {"message": "Re-processing started.", "prescription_id": str(prescription_id)}


@router.delete(
    "/{prescription_id}",
    status_code=204,
    summary="Delete a prescription",
)
async def delete_prescription(
    prescription_id: uuid.UUID,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
) -> None:
    result = await db.execute(
        select(Prescription).where(
            Prescription.id == prescription_id,
            Prescription.user_id == current_user.id,
        )
    )
    prescription = result.scalar_one_or_none()
    if not prescription:
        raise HTTPException(status_code=404, detail="Prescription not found.")
    await db.delete(prescription)
    await db.commit()

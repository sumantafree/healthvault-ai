"""
HealthVault AI — Medicines Routes
CRUD for medicine records, active medicine list, and status management.
Medicines are either auto-extracted from prescriptions or added manually.
"""
import uuid
from datetime import date
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from middleware.auth import CurrentUser
from models.family_member import FamilyMember
from models.medicine import Medicine
from schemas.medicine import MedicineCreate, MedicineResponse, MedicineUpdate

router = APIRouter(prefix="/medicines", tags=["Medicines"])


# ── Helpers ────────────────────────────────────────────────────────────────────

async def _verify_family_member(
    family_member_id: uuid.UUID,
    user_id: uuid.UUID,
    db: AsyncSession,
) -> FamilyMember:
    result = await db.execute(
        select(FamilyMember).where(
            FamilyMember.id == family_member_id,
            FamilyMember.user_id == user_id,
        )
    )
    member = result.scalar_one_or_none()
    if not member:
        raise HTTPException(status_code=404, detail="Family member not found.")
    return member


async def _get_medicine_or_404(
    medicine_id: uuid.UUID,
    user_id: uuid.UUID,
    db: AsyncSession,
) -> Medicine:
    result = await db.execute(
        select(Medicine)
        .join(FamilyMember, FamilyMember.id == Medicine.family_member_id)
        .where(
            Medicine.id == medicine_id,
            FamilyMember.user_id == user_id,
        )
    )
    medicine = result.scalar_one_or_none()
    if not medicine:
        raise HTTPException(status_code=404, detail="Medicine not found.")
    return medicine


# ── Routes ────────────────────────────────────────────────────────────────────

@router.get(
    "/",
    response_model=List[MedicineResponse],
    summary="List medicines for a family member",
)
async def list_medicines(
    family_member_id: uuid.UUID,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    active_only: bool = Query(False),
) -> List[Medicine]:
    await _verify_family_member(family_member_id, current_user.id, db)

    query = (
        select(Medicine)
        .where(Medicine.family_member_id == family_member_id)
        .order_by(Medicine.is_active.desc(), Medicine.name)
    )
    if active_only:
        query = query.where(Medicine.is_active == True)  # noqa: E712

    result = await db.execute(query)
    return result.scalars().all()


@router.get(
    "/active",
    response_model=List[MedicineResponse],
    summary="Get currently active medicines (not expired)",
)
async def list_active_medicines(
    family_member_id: uuid.UUID,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
) -> List[Medicine]:
    await _verify_family_member(family_member_id, current_user.id, db)

    today = date.today()
    result = await db.execute(
        select(Medicine)
        .where(
            Medicine.family_member_id == family_member_id,
            Medicine.is_active == True,  # noqa: E712
        )
        .order_by(Medicine.name)
    )
    medicines = result.scalars().all()

    # Filter out expired medicines
    active = []
    for m in medicines:
        if m.end_date is None or m.end_date >= today:
            active.append(m)
        else:
            # Auto-deactivate expired medicines
            m.is_active = False
            db.add(m)
    if any(m.is_active is False for m in medicines):
        await db.commit()

    return active


@router.post(
    "/",
    response_model=MedicineResponse,
    status_code=201,
    summary="Add a medicine manually",
)
async def create_medicine(
    payload: MedicineCreate,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
) -> Medicine:
    await _verify_family_member(payload.family_member_id, current_user.id, db)

    medicine = Medicine(**payload.model_dump())
    db.add(medicine)
    await db.commit()
    await db.refresh(medicine)
    return medicine


@router.get(
    "/{medicine_id}",
    response_model=MedicineResponse,
    summary="Get a medicine record",
)
async def get_medicine(
    medicine_id: uuid.UUID,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
) -> Medicine:
    return await _get_medicine_or_404(medicine_id, current_user.id, db)


@router.patch(
    "/{medicine_id}",
    response_model=MedicineResponse,
    summary="Update a medicine record",
)
async def update_medicine(
    medicine_id: uuid.UUID,
    payload: MedicineUpdate,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
) -> Medicine:
    medicine = await _get_medicine_or_404(medicine_id, current_user.id, db)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(medicine, field, value)
    db.add(medicine)
    await db.commit()
    await db.refresh(medicine)
    return medicine


@router.patch(
    "/{medicine_id}/toggle",
    response_model=MedicineResponse,
    summary="Toggle medicine active/inactive status",
)
async def toggle_medicine(
    medicine_id: uuid.UUID,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
) -> Medicine:
    medicine = await _get_medicine_or_404(medicine_id, current_user.id, db)
    medicine.is_active = not medicine.is_active
    db.add(medicine)
    await db.commit()
    await db.refresh(medicine)
    return medicine


@router.delete(
    "/{medicine_id}",
    status_code=204,
    summary="Delete a medicine record",
)
async def delete_medicine(
    medicine_id: uuid.UUID,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
) -> None:
    medicine = await _get_medicine_or_404(medicine_id, current_user.id, db)
    await db.delete(medicine)
    await db.commit()

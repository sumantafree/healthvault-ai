"""
HealthVault AI — Family Member Routes
Full CRUD for family health profiles.
"""
import uuid
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from middleware.auth import CurrentUser
from models.family_member import FamilyMember
from schemas.family_member import (
    FamilyMemberCreate,
    FamilyMemberResponse,
    FamilyMemberUpdate,
)

router = APIRouter(prefix="/family", tags=["Family Members"])


# ── Helpers ────────────────────────────────────────────────────────────────────

async def _get_member_or_404(
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
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Family member not found.",
        )
    return member


# ── Routes ────────────────────────────────────────────────────────────────────

@router.get("/", response_model=List[FamilyMemberResponse], summary="List all family members")
async def list_members(
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
) -> List[FamilyMember]:
    result = await db.execute(
        select(FamilyMember)
        .where(FamilyMember.user_id == current_user.id)
        .order_by(FamilyMember.is_primary.desc(), FamilyMember.name)
    )
    return result.scalars().all()


@router.post("/", response_model=FamilyMemberResponse, status_code=201, summary="Add a family member")
async def create_member(
    payload: FamilyMemberCreate,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
) -> FamilyMember:
    # Only one primary member allowed per user
    if payload.is_primary:
        existing_primary = await db.execute(
            select(FamilyMember).where(
                FamilyMember.user_id == current_user.id,
                FamilyMember.is_primary == True,  # noqa: E712
            )
        )
        if existing_primary.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="A primary member already exists. Update the existing one first.",
            )

    member = FamilyMember(
        user_id=current_user.id,
        **payload.model_dump(),
    )
    db.add(member)
    await db.commit()
    await db.refresh(member)
    return member


@router.get("/{member_id}", response_model=FamilyMemberResponse, summary="Get a family member")
async def get_member(
    member_id: uuid.UUID,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
) -> FamilyMember:
    return await _get_member_or_404(member_id, current_user.id, db)


@router.patch("/{member_id}", response_model=FamilyMemberResponse, summary="Update a family member")
async def update_member(
    member_id: uuid.UUID,
    payload: FamilyMemberUpdate,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
) -> FamilyMember:
    member = await _get_member_or_404(member_id, current_user.id, db)
    update_data = payload.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(member, field, value)
    db.add(member)
    await db.commit()
    await db.refresh(member)
    return member


@router.delete("/{member_id}", status_code=204, summary="Delete a family member")
async def delete_member(
    member_id: uuid.UUID,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
) -> None:
    member = await _get_member_or_404(member_id, current_user.id, db)
    await db.delete(member)
    await db.commit()

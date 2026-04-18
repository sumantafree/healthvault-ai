"""
HealthVault AI — Reminders Routes
CRUD for medicine / health reminders with WhatsApp delivery scheduling.
"""
import uuid
from datetime import datetime, timezone
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from middleware.auth import CurrentUser
from models.family_member import FamilyMember
from models.notification_log import NotificationLog
from models.reminder import Reminder
from scheduler import compute_next_send
from schemas.reminder import ReminderCreate, ReminderResponse, ReminderUpdate

router = APIRouter(prefix="/reminders", tags=["Reminders"])


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


async def _get_reminder_or_404(
    reminder_id: uuid.UUID,
    user_id: uuid.UUID,
    db: AsyncSession,
) -> Reminder:
    result = await db.execute(
        select(Reminder).where(
            Reminder.id == reminder_id,
            Reminder.user_id == user_id,
        )
    )
    reminder = result.scalar_one_or_none()
    if not reminder:
        raise HTTPException(status_code=404, detail="Reminder not found.")
    return reminder


# ── Routes ────────────────────────────────────────────────────────────────────


@router.get(
    "/",
    response_model=List[ReminderResponse],
    summary="List reminders for a family member",
)
async def list_reminders(
    family_member_id: uuid.UUID,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    active_only: bool = Query(False),
) -> List[Reminder]:
    await _verify_family_member(family_member_id, current_user.id, db)

    query = (
        select(Reminder)
        .where(Reminder.family_member_id == family_member_id)
        .order_by(Reminder.is_active.desc(), Reminder.reminder_time)
    )
    if active_only:
        query = query.where(Reminder.is_active == True)  # noqa: E712

    result = await db.execute(query)
    return result.scalars().all()


@router.post(
    "/",
    response_model=ReminderResponse,
    status_code=201,
    summary="Create a new reminder",
)
async def create_reminder(
    payload: ReminderCreate,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
) -> Reminder:
    await _verify_family_member(payload.family_member_id, current_user.id, db)

    reminder = Reminder(
        user_id=current_user.id,
        **payload.model_dump(),
    )
    # Set initial next_send_at
    reminder.next_send_at = compute_next_send(reminder, datetime.now(timezone.utc))

    db.add(reminder)
    await db.commit()
    await db.refresh(reminder)
    return reminder


@router.get(
    "/{reminder_id}",
    response_model=ReminderResponse,
    summary="Get a single reminder",
)
async def get_reminder(
    reminder_id: uuid.UUID,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
) -> Reminder:
    return await _get_reminder_or_404(reminder_id, current_user.id, db)


@router.patch(
    "/{reminder_id}",
    response_model=ReminderResponse,
    summary="Update a reminder",
)
async def update_reminder(
    reminder_id: uuid.UUID,
    payload: ReminderUpdate,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
) -> Reminder:
    reminder = await _get_reminder_or_404(reminder_id, current_user.id, db)

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(reminder, field, value)

    # Recompute schedule if time or frequency changed
    if payload.reminder_time is not None or payload.frequency is not None:
        reminder.next_send_at = compute_next_send(reminder, datetime.now(timezone.utc))

    db.add(reminder)
    await db.commit()
    await db.refresh(reminder)
    return reminder


@router.patch(
    "/{reminder_id}/toggle",
    response_model=ReminderResponse,
    summary="Toggle reminder active/inactive",
)
async def toggle_reminder(
    reminder_id: uuid.UUID,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
) -> Reminder:
    reminder = await _get_reminder_or_404(reminder_id, current_user.id, db)
    reminder.is_active = not reminder.is_active
    # Re-arm next_send_at when re-activating
    if reminder.is_active:
        reminder.next_send_at = compute_next_send(reminder, datetime.now(timezone.utc))
    db.add(reminder)
    await db.commit()
    await db.refresh(reminder)
    return reminder


@router.delete(
    "/{reminder_id}",
    status_code=204,
    summary="Delete a reminder",
)
async def delete_reminder(
    reminder_id: uuid.UUID,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
) -> None:
    reminder = await _get_reminder_or_404(reminder_id, current_user.id, db)
    await db.delete(reminder)
    await db.commit()


@router.get(
    "/{reminder_id}/logs",
    summary="Get delivery logs for a reminder",
)
async def get_reminder_logs(
    reminder_id: uuid.UUID,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    limit: int = Query(20, ge=1, le=100),
):
    reminder = await _get_reminder_or_404(reminder_id, current_user.id, db)

    result = await db.execute(
        select(NotificationLog)
        .where(NotificationLog.reminder_id == reminder.id)
        .order_by(NotificationLog.sent_at.desc())
        .limit(limit)
    )
    logs = result.scalars().all()

    return [
        {
            "id": str(entry.id),
            "channel": entry.channel,
            "recipient": entry.recipient,
            "status": entry.status,
            "sent_at": entry.sent_at.isoformat() if entry.sent_at else None,
            "provider_response": entry.provider_response,
        }
        for entry in logs
    ]

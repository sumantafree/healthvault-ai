"""
HealthVault AI — Background Scheduler
APScheduler AsyncIOScheduler: dispatches medicine reminders every minute.
"""
from datetime import datetime, timedelta, timezone
from typing import Optional

import structlog
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from sqlalchemy import select

from database import get_db_context
from models.family_member import FamilyMember
from models.medicine import Medicine
from models.notification_log import NotificationLog
from models.reminder import Reminder

log = structlog.get_logger()

# Module-level scheduler instance (started in app lifespan)
scheduler = AsyncIOScheduler(timezone="UTC")


# ── Scheduling helpers ────────────────────────────────────────────────────────


def compute_next_send(reminder: Reminder, after: datetime) -> datetime:
    """
    Compute the next UTC send datetime for a reminder given the current time.
    `reminder.reminder_time` is stored as a Python `time` object (UTC).
    """
    # Build the base datetime for today using the reminder's clock time
    base = after.replace(
        hour=reminder.reminder_time.hour,
        minute=reminder.reminder_time.minute,
        second=0,
        microsecond=0,
    )

    if reminder.frequency == "twice_daily":
        # Two sends per day: at reminder_time and at reminder_time + 12 h
        alt = base + timedelta(hours=12)
        candidates = [base, alt, base + timedelta(days=1), alt + timedelta(days=1)]
        future = [c for c in candidates if c > after]
        return min(future)

    if reminder.frequency == "weekly":
        next_dt = base if base > after else base + timedelta(weeks=1)
        return next_dt

    # Default: "daily" and anything unrecognised
    return base if base > after else base + timedelta(days=1)


# ── Dispatch job ──────────────────────────────────────────────────────────────


async def dispatch_due_reminders() -> None:
    """
    Scheduler job (runs every minute):
    Query all active reminders whose next_send_at ≤ now and send WhatsApp messages.
    """
    from utils.whatsapp import format_reminder_message, send_whatsapp_message  # local to avoid circular

    now = datetime.now(timezone.utc)

    try:
        async with get_db_context() as db:
            result = await db.execute(
                select(Reminder).where(
                    Reminder.is_active == True,  # noqa: E712
                    Reminder.next_send_at <= now,
                    Reminder.whatsapp_number.is_not(None),
                )
            )
            due = result.scalars().all()

            if not due:
                return

            log.info("scheduler_dispatching", count=len(due))

            for reminder in due:
                # Resolve member name
                member_res = await db.execute(
                    select(FamilyMember).where(FamilyMember.id == reminder.family_member_id)
                )
                member = member_res.scalar_one_or_none()
                member_name = member.name if member else "Family Member"

                # Resolve medicine name (if linked)
                medicine_name: Optional[str] = None
                if reminder.medicine_id:
                    med_res = await db.execute(
                        select(Medicine).where(Medicine.id == reminder.medicine_id)
                    )
                    med = med_res.scalar_one_or_none()
                    medicine_name = med.name if med else None

                # Build and send
                body = format_reminder_message(
                    title=reminder.title,
                    member_name=member_name,
                    medicine_name=medicine_name,
                    message=reminder.message,
                )
                result_dict = await send_whatsapp_message(reminder.whatsapp_number, body)

                # Persist notification log
                db.add(
                    NotificationLog(
                        user_id=reminder.user_id,
                        family_member_id=reminder.family_member_id,
                        reminder_id=reminder.id,
                        channel="whatsapp",
                        recipient=reminder.whatsapp_number,
                        message=body,
                        status=result_dict.get("status", "unknown"),
                        provider_response=result_dict,
                    )
                )

                # Advance timestamps
                reminder.last_sent_at = now
                reminder.next_send_at = compute_next_send(reminder, now)
                db.add(reminder)

                log.info(
                    "reminder_dispatched",
                    id=str(reminder.id),
                    status=result_dict.get("status"),
                    next=reminder.next_send_at.isoformat(),
                )

            await db.commit()

    except Exception as exc:
        log.error("scheduler_job_error", error=str(exc), exc_info=True)


# ── Lifecycle ─────────────────────────────────────────────────────────────────


def start_scheduler() -> None:
    """Start the background scheduler. Call once at app startup."""
    scheduler.add_job(
        dispatch_due_reminders,
        trigger=IntervalTrigger(minutes=1),
        id="dispatch_reminders",
        replace_existing=True,
        max_instances=1,
        misfire_grace_time=30,
    )
    scheduler.start()
    log.info("scheduler_started", jobs=len(scheduler.get_jobs()))


def stop_scheduler() -> None:
    """Gracefully stop the scheduler. Call on app shutdown."""
    if scheduler.running:
        scheduler.shutdown(wait=False)
        log.info("scheduler_stopped")

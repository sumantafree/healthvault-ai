"""
HealthVault AI — WhatsApp Notification Utility (Twilio)
Async wrapper around the synchronous Twilio SDK.
"""
import asyncio
from typing import Optional

import structlog

from config import settings

log = structlog.get_logger()


async def send_whatsapp_message(to: str, body: str) -> dict:
    """
    Send a WhatsApp message via Twilio.
    Returns a result dict: {"status": "sent"|"failed"|"skipped", ...}
    """
    if not settings.TWILIO_ACCOUNT_SID or not settings.TWILIO_AUTH_TOKEN:
        log.warning("twilio_not_configured", to=to)
        return {"status": "skipped", "reason": "Twilio credentials not configured"}

    try:
        from twilio.rest import Client as TwilioClient  # lazy import

        client = TwilioClient(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)

        # Normalise the recipient number
        recipient = to if to.startswith("whatsapp:") else f"whatsapp:{to}"

        # Twilio's SDK is synchronous — offload to thread pool
        loop = asyncio.get_running_loop()
        message = await loop.run_in_executor(
            None,
            lambda: client.messages.create(
                from_=settings.TWILIO_WHATSAPP_FROM,
                to=recipient,
                body=body,
            ),
        )

        log.info("whatsapp_sent", to=to, sid=message.sid, status=message.status)
        return {"status": "sent", "sid": message.sid, "twilio_status": message.status}

    except Exception as exc:
        log.error("whatsapp_failed", to=to, error=str(exc))
        return {"status": "failed", "error": str(exc)}


def format_reminder_message(
    title: str,
    member_name: str,
    medicine_name: Optional[str],
    message: Optional[str],
) -> str:
    """
    Build the WhatsApp message body for a medicine reminder.
    Uses plain Twilio-safe text with minimal markdown.
    """
    lines = [
        "*HealthVault AI Reminder*",
        f"👤 For: {member_name}",
    ]
    if medicine_name:
        lines.append(f"💊 Medicine: {medicine_name}")
    lines.append(f"📌 {title}")
    if message:
        lines.append(f"\n{message}")
    lines.append("\n_HealthVault AI — Family Health Intelligence_")
    return "\n".join(lines)

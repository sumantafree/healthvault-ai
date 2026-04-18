"""
HealthVault AI — Reminders Route + Scheduler Tests
"""
from datetime import datetime, time, timedelta, timezone

import pytest

from models.family_member import FamilyMember
from models.reminder import Reminder
from scheduler import compute_next_send


# ── compute_next_send unit tests ──────────────────────────────────────────────


class TestComputeNextSend:
    def _reminder(self, t: time, frequency: str = "daily") -> Reminder:
        r = Reminder.__new__(Reminder)
        r.reminder_time = t
        r.frequency = frequency
        return r

    def test_daily_future_today(self):
        now = datetime(2024, 6, 1, 10, 0, tzinfo=timezone.utc)
        reminder = self._reminder(time(14, 0), "daily")
        nxt = compute_next_send(reminder, now)
        assert nxt == datetime(2024, 6, 1, 14, 0, tzinfo=timezone.utc)

    def test_daily_rolls_to_tomorrow(self):
        now = datetime(2024, 6, 1, 15, 0, tzinfo=timezone.utc)
        reminder = self._reminder(time(14, 0), "daily")
        nxt = compute_next_send(reminder, now)
        assert nxt == datetime(2024, 6, 2, 14, 0, tzinfo=timezone.utc)

    def test_weekly_future(self):
        now = datetime(2024, 6, 1, 10, 0, tzinfo=timezone.utc)
        reminder = self._reminder(time(9, 0), "weekly")
        nxt = compute_next_send(reminder, now)
        assert nxt == datetime(2024, 6, 8, 9, 0, tzinfo=timezone.utc)

    def test_twice_daily_first_slot(self):
        now = datetime(2024, 6, 1, 7, 0, tzinfo=timezone.utc)
        reminder = self._reminder(time(8, 0), "twice_daily")
        nxt = compute_next_send(reminder, now)
        assert nxt == datetime(2024, 6, 1, 8, 0, tzinfo=timezone.utc)

    def test_twice_daily_second_slot(self):
        now = datetime(2024, 6, 1, 9, 0, tzinfo=timezone.utc)
        reminder = self._reminder(time(8, 0), "twice_daily")
        nxt = compute_next_send(reminder, now)
        assert nxt == datetime(2024, 6, 1, 20, 0, tzinfo=timezone.utc)  # 8+12

    def test_unknown_frequency_defaults_to_daily(self):
        now = datetime(2024, 6, 1, 10, 0, tzinfo=timezone.utc)
        reminder = self._reminder(time(11, 0), "custom")
        nxt = compute_next_send(reminder, now)
        assert nxt == datetime(2024, 6, 1, 11, 0, tzinfo=timezone.utc)


# ── API route tests ───────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_list_reminders_no_member(client):
    fake_id = "00000000-0000-0000-0000-000000000000"
    response = await client.get(f"/api/v1/reminders/?family_member_id={fake_id}")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_create_reminder(client, test_user, db_session):
    member = FamilyMember(user_id=test_user.id, name="Reminder Patient")
    db_session.add(member)
    await db_session.commit()
    await db_session.refresh(member)

    payload = {
        "family_member_id": str(member.id),
        "title": "Take Metformin",
        "reminder_time": "08:00:00",
        "frequency": "daily",
        "whatsapp_number": "+1234567890",
    }
    response = await client.post("/api/v1/reminders/", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Take Metformin"
    assert data["frequency"] == "daily"
    assert data["is_active"] is True
    assert data["next_send_at"] is not None


@pytest.mark.asyncio
async def test_toggle_reminder(client, test_user, db_session):
    member = FamilyMember(user_id=test_user.id, name="Toggle Reminder Patient")
    db_session.add(member)
    await db_session.commit()
    await db_session.refresh(member)

    reminder = Reminder(
        user_id=test_user.id,
        family_member_id=member.id,
        title="Morning Pills",
        reminder_time=time(7, 30),
        frequency="daily",
        is_active=True,
    )
    db_session.add(reminder)
    await db_session.commit()
    await db_session.refresh(reminder)

    response = await client.patch(f"/api/v1/reminders/{reminder.id}/toggle")
    assert response.status_code == 200
    assert response.json()["is_active"] is False

    # Toggle back
    response = await client.patch(f"/api/v1/reminders/{reminder.id}/toggle")
    assert response.status_code == 200
    assert response.json()["is_active"] is True


@pytest.mark.asyncio
async def test_update_reminder(client, test_user, db_session):
    member = FamilyMember(user_id=test_user.id, name="Update Reminder Patient")
    db_session.add(member)
    await db_session.commit()
    await db_session.refresh(member)

    reminder = Reminder(
        user_id=test_user.id,
        family_member_id=member.id,
        title="Evening Dose",
        reminder_time=time(18, 0),
        frequency="daily",
        is_active=True,
    )
    db_session.add(reminder)
    await db_session.commit()
    await db_session.refresh(reminder)

    response = await client.patch(
        f"/api/v1/reminders/{reminder.id}",
        json={"title": "Evening Dose Updated", "whatsapp_number": "+9876543210"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Evening Dose Updated"
    assert data["whatsapp_number"] == "+9876543210"


@pytest.mark.asyncio
async def test_delete_reminder(client, test_user, db_session):
    member = FamilyMember(user_id=test_user.id, name="Delete Reminder Patient")
    db_session.add(member)
    await db_session.commit()
    await db_session.refresh(member)

    reminder = Reminder(
        user_id=test_user.id,
        family_member_id=member.id,
        title="To Delete",
        reminder_time=time(9, 0),
        frequency="daily",
        is_active=True,
    )
    db_session.add(reminder)
    await db_session.commit()
    await db_session.refresh(reminder)

    response = await client.delete(f"/api/v1/reminders/{reminder.id}")
    assert response.status_code == 204

    check = await client.get(f"/api/v1/reminders/{reminder.id}")
    assert check.status_code == 404


@pytest.mark.asyncio
async def test_list_reminders_active_only(client, test_user, db_session):
    member = FamilyMember(user_id=test_user.id, name="Active Only Patient")
    db_session.add(member)
    await db_session.commit()
    await db_session.refresh(member)

    active = Reminder(
        user_id=test_user.id,
        family_member_id=member.id,
        title="Active Reminder",
        reminder_time=time(8, 0),
        frequency="daily",
        is_active=True,
    )
    inactive = Reminder(
        user_id=test_user.id,
        family_member_id=member.id,
        title="Inactive Reminder",
        reminder_time=time(9, 0),
        frequency="daily",
        is_active=False,
    )
    db_session.add_all([active, inactive])
    await db_session.commit()

    response = await client.get(
        f"/api/v1/reminders/?family_member_id={member.id}&active_only=true"
    )
    assert response.status_code == 200
    titles = [r["title"] for r in response.json()]
    assert "Active Reminder" in titles
    assert "Inactive Reminder" not in titles

"""
HealthVault AI — AI Insights API Route Tests
"""
import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch

import pytest

from models.ai_insight import AIInsight


@pytest.mark.asyncio
async def test_list_insights_no_member(client):
    """Returns 404 for unknown family member."""
    fake_id = "00000000-0000-0000-0000-000000000000"
    response = await client.get(f"/api/v1/insights/?family_member_id={fake_id}")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_latest_insight_no_data(client, test_user, db_session):
    """Returns 404 when no insights exist for a member."""
    from models.family_member import FamilyMember

    member = FamilyMember(
        user_id=test_user.id,
        name="Test Child",
    )
    db_session.add(member)
    await db_session.commit()
    await db_session.refresh(member)

    response = await client.get(f"/api/v1/insights/latest?family_member_id={member.id}")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_reanalyze_report_not_found(client):
    """Returns 404 for a non-existent report."""
    fake_id = "00000000-0000-0000-0000-000000000000"
    response = await client.post(f"/api/v1/insights/reanalyze/{fake_id}")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_list_insights_returns_data(client, test_user, db_session):
    """Returns insights list for a valid member."""
    from models.family_member import FamilyMember

    member = FamilyMember(user_id=test_user.id, name="Parent")
    db_session.add(member)
    await db_session.commit()
    await db_session.refresh(member)

    insight = AIInsight(
        family_member_id=member.id,
        summary="All values appear within normal reference ranges.",
        risk_level="low",
        risk_factors=[],
        recommendations={"items": []},
    )
    db_session.add(insight)
    await db_session.commit()

    response = await client.get(f"/api/v1/insights/?family_member_id={member.id}")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1
    assert data[0]["risk_level"] == "low"
    assert "disclaimer" in data[0]

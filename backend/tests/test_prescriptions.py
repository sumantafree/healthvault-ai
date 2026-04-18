"""
HealthVault AI — Prescription & Medicine Route Tests
"""
import json
import uuid
from datetime import date
from unittest.mock import AsyncMock, patch

import pytest

from ai.prescription_parser import ExtractedMedicine, ParsedPrescription, _safe_parse
from models.family_member import FamilyMember
from models.medicine import Medicine
from models.prescription import Prescription


# ── Parser unit tests ─────────────────────────────────────────────────────────

class TestPrescriptionParser:
    def test_safe_parse_valid_json(self):
        raw = json.dumps({
            "doctor_name": "Dr. Smith",
            "hospital_name": "City Hospital",
            "prescribed_date": "2024-03-01",
            "valid_until": "2024-06-01",
            "medicines": [
                {
                    "name": "Amoxicillin",
                    "generic_name": "Amoxicillin trihydrate",
                    "dosage": "500mg",
                    "form": "capsule",
                    "frequency": "3 times daily",
                    "instructions": "Take with food",
                    "duration_days": 7,
                }
            ],
        })
        result = _safe_parse(raw)
        assert isinstance(result, ParsedPrescription)
        assert result.doctor_name == "Dr. Smith"
        assert len(result.medicines) == 1
        assert result.medicines[0].name == "Amoxicillin"
        assert result.medicines[0].dosage == "500mg"
        assert result.medicines[0].duration_days == 7

    def test_safe_parse_empty_medicines(self):
        raw = json.dumps({"medicines": []})
        result = _safe_parse(raw)
        assert result.medicines == []

    def test_safe_parse_invalid_json_returns_empty(self):
        result = _safe_parse("not json {{{")
        assert isinstance(result, ParsedPrescription)
        assert result.medicines == []

    def test_medicine_form_normalization(self):
        med = ExtractedMedicine(name="Test", form="TABLET")
        assert med.form == "tablet"

    def test_medicine_invalid_form_becomes_other(self):
        med = ExtractedMedicine(name="Test", form="unknown_form_xyz")
        assert med.form == "other"

    def test_prescribed_date_parsing(self):
        raw = json.dumps({"prescribed_date": "2024-05-15", "medicines": []})
        result = _safe_parse(raw)
        assert result.prescribed_date_as_date == date(2024, 5, 15)

    def test_invalid_date_returns_none(self):
        raw = json.dumps({"prescribed_date": "not-a-date", "medicines": []})
        result = _safe_parse(raw)
        assert result.prescribed_date_as_date is None

    def test_medicines_without_name_are_skipped(self):
        raw = json.dumps({
            "medicines": [
                {"name": "Paracetamol", "dosage": "500mg"},
                {"dosage": "100mg"},  # no name — should be skipped
            ]
        })
        result = _safe_parse(raw)
        assert len(result.medicines) == 1
        assert result.medicines[0].name == "Paracetamol"


# ── API route tests ───────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_list_prescriptions_no_member(client):
    fake_id = "00000000-0000-0000-0000-000000000000"
    response = await client.get(f"/api/v1/prescriptions/?family_member_id={fake_id}")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_list_medicines_no_member(client):
    fake_id = "00000000-0000-0000-0000-000000000000"
    response = await client.get(f"/api/v1/medicines/?family_member_id={fake_id}")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_list_medicines_returns_data(client, test_user, db_session):
    member = FamilyMember(user_id=test_user.id, name="Test Patient")
    db_session.add(member)
    await db_session.commit()
    await db_session.refresh(member)

    medicine = Medicine(
        family_member_id=member.id,
        name="Metformin",
        dosage="500mg",
        frequency="twice daily",
        is_active=True,
    )
    db_session.add(medicine)
    await db_session.commit()

    response = await client.get(f"/api/v1/medicines/?family_member_id={member.id}")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1
    assert data[0]["name"] == "Metformin"


@pytest.mark.asyncio
async def test_create_medicine_manual(client, test_user, db_session):
    member = FamilyMember(user_id=test_user.id, name="Manual Med Patient")
    db_session.add(member)
    await db_session.commit()
    await db_session.refresh(member)

    payload = {
        "family_member_id": str(member.id),
        "name": "Vitamin D",
        "dosage": "1000 IU",
        "frequency": "once daily",
        "form": "tablet",
        "is_active": True,
    }
    response = await client.post("/api/v1/medicines/", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Vitamin D"
    assert data["is_active"] is True


@pytest.mark.asyncio
async def test_toggle_medicine(client, test_user, db_session):
    member = FamilyMember(user_id=test_user.id, name="Toggle Patient")
    db_session.add(member)
    await db_session.commit()
    await db_session.refresh(member)

    medicine = Medicine(
        family_member_id=member.id,
        name="Aspirin",
        is_active=True,
    )
    db_session.add(medicine)
    await db_session.commit()
    await db_session.refresh(medicine)

    response = await client.patch(f"/api/v1/medicines/{medicine.id}/toggle")
    assert response.status_code == 200
    assert response.json()["is_active"] is False


@pytest.mark.asyncio
async def test_update_medicine(client, test_user, db_session):
    member = FamilyMember(user_id=test_user.id, name="Update Patient")
    db_session.add(member)
    await db_session.commit()
    await db_session.refresh(member)

    medicine = Medicine(
        family_member_id=member.id,
        name="Lisinopril",
        dosage="5mg",
        is_active=True,
    )
    db_session.add(medicine)
    await db_session.commit()
    await db_session.refresh(medicine)

    response = await client.patch(
        f"/api/v1/medicines/{medicine.id}",
        json={"dosage": "10mg", "frequency": "once daily"},
    )
    assert response.status_code == 200
    assert response.json()["dosage"] == "10mg"


@pytest.mark.asyncio
async def test_delete_medicine(client, test_user, db_session):
    member = FamilyMember(user_id=test_user.id, name="Delete Patient")
    db_session.add(member)
    await db_session.commit()
    await db_session.refresh(member)

    medicine = Medicine(family_member_id=member.id, name="Atorvastatin", is_active=True)
    db_session.add(medicine)
    await db_session.commit()
    await db_session.refresh(medicine)

    response = await client.delete(f"/api/v1/medicines/{medicine.id}")
    assert response.status_code == 204

    check = await client.get(f"/api/v1/medicines/{medicine.id}")
    assert check.status_code == 404


@pytest.mark.asyncio
async def test_active_medicines_excludes_expired(client, test_user, db_session):
    from datetime import timedelta
    member = FamilyMember(user_id=test_user.id, name="Expired Med Patient")
    db_session.add(member)
    await db_session.commit()
    await db_session.refresh(member)

    active_med = Medicine(
        family_member_id=member.id, name="Active Drug",
        is_active=True,
        end_date=date.today() + timedelta(days=10),
    )
    expired_med = Medicine(
        family_member_id=member.id, name="Expired Drug",
        is_active=True,
        end_date=date(2020, 1, 1),  # expired
    )
    db_session.add_all([active_med, expired_med])
    await db_session.commit()

    response = await client.get(f"/api/v1/medicines/active?family_member_id={member.id}")
    assert response.status_code == 200
    names = [m["name"] for m in response.json()]
    assert "Active Drug" in names
    assert "Expired Drug" not in names

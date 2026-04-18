"""
HealthVault AI — Family Member Route Tests
"""
import pytest


MEMBER_PAYLOAD = {
    "name": "Jane Doe",
    "gender": "female",
    "blood_type": "O+",
    "date_of_birth": "1990-05-15",
    "height_cm": 165.0,
    "weight_kg": 60.0,
    "allergies": ["penicillin"],
    "is_primary": False,
}


@pytest.mark.asyncio
async def test_create_family_member(client):
    response = await client.post("/api/v1/family/", json=MEMBER_PAYLOAD)
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Jane Doe"
    assert data["blood_type"] == "O+"
    assert data["age"] is not None


@pytest.mark.asyncio
async def test_list_family_members(client):
    # Create two members
    await client.post("/api/v1/family/", json=MEMBER_PAYLOAD)
    await client.post("/api/v1/family/", json={**MEMBER_PAYLOAD, "name": "John Doe"})

    response = await client.get("/api/v1/family/")
    assert response.status_code == 200
    assert len(response.json()) >= 2


@pytest.mark.asyncio
async def test_get_family_member(client):
    create = await client.post("/api/v1/family/", json=MEMBER_PAYLOAD)
    member_id = create.json()["id"]

    response = await client.get(f"/api/v1/family/{member_id}")
    assert response.status_code == 200
    assert response.json()["id"] == member_id


@pytest.mark.asyncio
async def test_update_family_member(client):
    create = await client.post("/api/v1/family/", json=MEMBER_PAYLOAD)
    member_id = create.json()["id"]

    response = await client.patch(
        f"/api/v1/family/{member_id}",
        json={"weight_kg": 62.5, "allergies": ["penicillin", "sulfa"]},
    )
    assert response.status_code == 200
    assert response.json()["weight_kg"] == 62.5


@pytest.mark.asyncio
async def test_delete_family_member(client):
    create = await client.post("/api/v1/family/", json=MEMBER_PAYLOAD)
    member_id = create.json()["id"]

    delete = await client.delete(f"/api/v1/family/{member_id}")
    assert delete.status_code == 204

    get = await client.get(f"/api/v1/family/{member_id}")
    assert get.status_code == 404


@pytest.mark.asyncio
async def test_get_nonexistent_member_returns_404(client):
    response = await client.get("/api/v1/family/00000000-0000-0000-0000-000000000000")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_only_one_primary_member_allowed(client):
    await client.post("/api/v1/family/", json={**MEMBER_PAYLOAD, "is_primary": True})
    response = await client.post("/api/v1/family/", json={**MEMBER_PAYLOAD, "is_primary": True})
    assert response.status_code == 409

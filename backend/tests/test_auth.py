"""
HealthVault AI — Auth Route Tests
"""
import pytest


@pytest.mark.asyncio
async def test_get_me_returns_user(client, test_user):
    response = await client.get("/api/v1/auth/me")
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == test_user.email
    assert data["id"] == str(test_user.id)


@pytest.mark.asyncio
async def test_sync_user(client, test_user):
    response = await client.post("/api/v1/auth/me")
    assert response.status_code == 200
    assert response.json()["email"] == test_user.email


@pytest.mark.asyncio
async def test_update_me(client):
    response = await client.patch(
        "/api/v1/auth/me",
        json={"full_name": "Updated Name", "timezone": "Asia/Kolkata"},
    )
    assert response.status_code == 200
    assert response.json()["full_name"] == "Updated Name"


@pytest.mark.asyncio
async def test_deactivate_me(client):
    response = await client.delete("/api/v1/auth/me")
    assert response.status_code == 204


@pytest.mark.asyncio
async def test_health_check(client):
    response = await client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"

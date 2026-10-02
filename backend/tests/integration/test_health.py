"""Integration tests for Liveness /health endpoint."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_root_health(async_client: AsyncClient):
    response = await async_client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "HEALTHY"
    assert data["app_name"] == "NEXUS Test Engine"
    assert data["environment"] == "testing"
    assert "timestamp" in data


@pytest.mark.asyncio
async def test_api_v1_health(async_client: AsyncClient):
    response = await async_client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "HEALTHY"

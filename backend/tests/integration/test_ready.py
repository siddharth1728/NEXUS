"""Integration tests for Readiness /ready endpoint."""

from unittest.mock import AsyncMock, patch

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_ready_healthy(async_client: AsyncClient):
    with patch(
        "app.api.v1.endpoints.health.check_database_connection", new_callable=AsyncMock
    ) as mock_db:
        mock_db.return_value = (True, 2.34, None)
        response = await async_client.get("/ready")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "HEALTHY"
        assert "database" in data["components"]
        assert data["components"]["database"]["status"] == "HEALTHY"
        assert data["components"]["database"]["latency_ms"] == 2.34


@pytest.mark.asyncio
async def test_ready_unhealthy(async_client: AsyncClient):
    with patch(
        "app.api.v1.endpoints.health.check_database_connection", new_callable=AsyncMock
    ) as mock_db:
        mock_db.return_value = (False, 10.5, "Connection refused: port 5432")
        response = await async_client.get("/ready")
        assert response.status_code == 503
        data = response.json()
        assert data["status"] == "UNHEALTHY"
        assert data["components"]["database"]["status"] == "UNHEALTHY"
        assert "Connection refused" in data["components"]["database"]["details"]["error"]


@pytest.mark.asyncio
async def test_api_v1_ready(async_client: AsyncClient):
    with patch(
        "app.api.v1.endpoints.health.check_database_connection", new_callable=AsyncMock
    ) as mock_db:
        mock_db.return_value = (True, 1.0, None)
        response = await async_client.get("/api/v1/ready")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "HEALTHY"

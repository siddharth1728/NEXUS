"""Integration tests for correlation ID and latency tracking middleware."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_correlation_id_generated_and_returned(async_client: AsyncClient):
    response = await async_client.get("/health")
    assert response.status_code == 200
    assert "X-Request-ID" in response.headers
    assert len(response.headers["X-Request-ID"]) > 10
    assert "X-Process-Time-Ms" in response.headers


@pytest.mark.asyncio
async def test_correlation_id_preserved_when_passed(async_client: AsyncClient):
    custom_id = "custom-trace-id-abc-123"
    response = await async_client.get("/health", headers={"X-Request-ID": custom_id})
    assert response.status_code == 200
    assert response.headers["X-Request-ID"] == custom_id

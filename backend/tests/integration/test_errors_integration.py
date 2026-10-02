"""Integration tests for error envelopes and exception handlers."""

import pytest
from fastapi import APIRouter
from httpx import ASGITransport, AsyncClient

from app.core.config import Settings
from app.core.errors import ConflictError, GraphCycleError, NotFoundError, ValidationError
from app.main import create_app


@pytest.mark.asyncio
async def test_404_not_found_envelope(async_client: AsyncClient) -> None:
    response = await async_client.get("/non-existent-endpoint-404")
    assert response.status_code == 404
    data = response.json()
    assert "error" in data
    assert data["error"]["code"] == "RESOURCE_NOT_FOUND"
    assert data["error"]["request_id"] is not None


@pytest.mark.asyncio
async def test_custom_app_error_handlers(test_settings: Settings) -> None:
    # Create test router raising various domain errors
    router = APIRouter()

    @router.get("/test-not-found")
    async def raise_not_found():  # type: ignore
        raise NotFoundError("Task", "task-abc")

    @router.get("/test-cycle")
    async def raise_cycle():  # type: ignore
        raise GraphCycleError(["A", "B", "A"])

    @router.get("/test-conflict")
    async def raise_conflict():  # type: ignore
        raise ConflictError("Task state modified concurrently")

    @router.get("/test-validation")
    async def raise_validation():  # type: ignore
        raise ValidationError("Field invalid", details={"param": "due_date"})

    @router.get("/test-unhandled")
    async def raise_unhandled():  # type: ignore
        raise RuntimeError("Unexpected server bug")

    app = create_app(test_settings)
    app.include_router(router)

    transport = ASGITransport(app=app, raise_app_exceptions=False)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        # 1. NotFoundError (404)
        resp = await client.get("/test-not-found")
        assert resp.status_code == 404
        assert resp.json()["error"]["code"] == "RESOURCE_NOT_FOUND"

        # 2. GraphCycleError (400)
        resp = await client.get("/test-cycle")
        assert resp.status_code == 400
        assert resp.json()["error"]["code"] == "DEPENDENCY_CYCLE_DETECTED"
        assert resp.json()["error"]["details"]["cycle_path"] == ["A", "B", "A"]

        # 3. ConflictError (409)
        resp = await client.get("/test-conflict")
        assert resp.status_code == 409
        assert resp.json()["error"]["code"] == "STATE_CONFLICT"

        # 4. ValidationError (422)
        resp = await client.get("/test-validation")
        assert resp.status_code == 422
        assert resp.json()["error"]["code"] == "VALIDATION_FAILED"

        # 5. Unhandled RuntimeError (500)
        resp = await client.get("/test-unhandled")
        assert resp.status_code == 500
        assert resp.json()["error"]["code"] == "INTERNAL_SERVER_ERROR"
        assert resp.json()["error"]["message"] == "An unexpected internal server error occurred."

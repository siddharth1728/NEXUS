"""Integration tests for Documents API endpoints."""

import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enums import ExtractionJobStatus
from app.models.tenant import Tenant


@pytest.fixture
async def active_tenant(in_memory_db_session: AsyncSession) -> Tenant:
    tenant = Tenant(name="API Test Tenant", id=uuid.UUID("00000000-0000-4000-8000-000000000001"))
    in_memory_db_session.add(tenant)
    await in_memory_db_session.commit()
    return tenant


@pytest.mark.asyncio
@pytest.mark.integration
async def test_create_and_get_document(async_client: AsyncClient, active_tenant: Tenant) -> None:
    payload = {
        "title": "Onboarding Guide",
        "source_type": "pdf",
        "sha256_hash": "dummyhash",
    }

    # Create doc
    create_resp = await async_client.post("/api/v1/documents", json=payload)
    assert create_resp.status_code == 201
    doc_id = create_resp.json()["id"]

    # Get doc
    get_resp = await async_client.get(f"/api/v1/documents/{doc_id}")
    assert get_resp.status_code == 200
    assert get_resp.json()["title"] == payload["title"]


@pytest.mark.asyncio
@pytest.mark.integration
async def test_extraction_job_lifecycle(async_client: AsyncClient, active_tenant: Tenant) -> None:
    # 1. Create doc
    doc_resp = await async_client.post(
        "/api/v1/documents",
        json={"title": "Data Sheet", "source_type": "docx", "sha256_hash": "hash"},
    )
    doc_id = doc_resp.json()["id"]

    # 2. Create job
    job_resp = await async_client.post("/api/v1/documents/jobs", json={"document_id": doc_id})
    assert job_resp.status_code == 201
    job_id = job_resp.json()["id"]
    assert job_resp.json()["status"] == ExtractionJobStatus.PENDING

    # 3. Invalid transition (PENDING -> COMPLETED)
    invalid_resp = await async_client.post(
        f"/api/v1/documents/jobs/{job_id}/transition",
        json={"new_status": ExtractionJobStatus.COMPLETED},
    )
    assert invalid_resp.status_code == 409

    # 4. Valid transition (PENDING -> RUNNING)
    run_resp = await async_client.post(
        f"/api/v1/documents/jobs/{job_id}/transition",
        json={"new_status": ExtractionJobStatus.RUNNING},
    )
    assert run_resp.status_code == 200
    assert run_resp.json()["status"] == ExtractionJobStatus.RUNNING

    # 5. Valid transition (RUNNING -> FAILED)
    fail_resp = await async_client.post(
        f"/api/v1/documents/jobs/{job_id}/transition",
        json={"new_status": ExtractionJobStatus.FAILED, "error_category": "parse_error"},
    )
    assert fail_resp.status_code == 200
    assert fail_resp.json()["error_category"] == "parse_error"

    # 6. Retry (FAILED -> RETRYING)
    retry_resp = await async_client.post(
        f"/api/v1/documents/jobs/{job_id}/transition",
        json={"new_status": ExtractionJobStatus.RETRYING},
    )
    assert retry_resp.status_code == 200
    assert retry_resp.json()["retry_count"] == 1

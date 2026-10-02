"""Integration tests for Document endpoints."""

import uuid
from typing import Any

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
@pytest.mark.integration
async def test_upload_document(
    async_client: AsyncClient, test_app: Any, in_memory_db_session: Any
) -> None:
    from collections.abc import AsyncGenerator

    from app.api.deps import get_db_session

    async def override_get_db() -> AsyncGenerator[Any, None]:
        yield in_memory_db_session

    test_app.dependency_overrides[get_db_session] = override_get_db

    # 0. Setup tenant
    tenant_id = uuid.UUID("00000000-0000-4000-8000-000000000001")
    from app.models.tenant import Tenant

    tenant = Tenant(id=tenant_id, name="Test Tenant")
    in_memory_db_session.add(tenant)
    await in_memory_db_session.commit()

    # 1. Create a dummy file
    file_content = b"# Test Document\n\nThis is a test."
    files = {"file": ("test.md", file_content, "text/markdown")}

    # 2. Upload
    response = await async_client.post("/api/v1/documents/upload", files=files)

    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "test.md"
    assert data["source_type"] == "md"
    assert data["processing_status"] == "COMPLETED"

    document_id = data["id"]

    # 3. Fetch chunks
    chunks_response = await async_client.get(f"/api/v1/documents/{document_id}/chunks")
    assert chunks_response.status_code == 200
    chunks = chunks_response.json()
    assert len(chunks) == 2

    assert chunks[0]["structural_type"] == "heading"
    assert chunks[0]["content"] == "# Test Document"
    assert chunks[0]["source_location"]["section"] == "Test Document"

    assert chunks[1]["structural_type"] == "paragraph"
    assert chunks[1]["content"] == "This is a test."
    assert chunks[1]["source_location"]["section"] == "Test Document"

"""Integration tests for AI Extraction API."""

import uuid
from typing import Any
from unittest.mock import AsyncMock

import pytest
import pytest_asyncio
from httpx import AsyncClient

from app.core.ai.gateway import AIGateway
from app.core.ai.models import AIRequest, AIResponse
from app.models.document import Document, DocumentChunk


@pytest_asyncio.fixture
async def test_document(in_memory_db_session: Any) -> Document:
    tenant_id = uuid.UUID("00000000-0000-4000-8000-000000000001")
    from app.models.tenant import Tenant

    # Need to make sure Tenant exists
    tenant = await in_memory_db_session.get(Tenant, tenant_id)
    if not tenant:
        tenant = Tenant(id=tenant_id, name="Test Tenant")
        in_memory_db_session.add(tenant)

    doc = Document(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        title="Test Doc",
        source_type="md",
        sha256_hash="fakehash",
    )
    in_memory_db_session.add(doc)
    await in_memory_db_session.commit()
    return doc


@pytest_asyncio.fixture
async def test_chunk(in_memory_db_session: Any, test_document: Document) -> DocumentChunk:
    chunk = DocumentChunk(
        id=uuid.uuid4(),
        document_id=test_document.id,
        chunk_index=0,
        content="Test content chunk.",
        source_location={"section": "Body", "block_index": 0},
    )
    in_memory_db_session.add(chunk)
    await in_memory_db_session.commit()
    return chunk


@pytest.mark.asyncio
@pytest.mark.integration
async def test_extract_chunk_endpoint(
    async_client: AsyncClient, test_app: Any, in_memory_db_session: Any, test_chunk: DocumentChunk
) -> None:
    # 1. Override dependencies
    from collections.abc import AsyncGenerator

    from app.api.deps import get_db_session

    async def override_get_db() -> AsyncGenerator[Any, None]:
        yield in_memory_db_session

    test_app.dependency_overrides[get_db_session] = override_get_db

    from unittest.mock import MagicMock

    mock_gateway = MagicMock(spec=AIGateway)
    mock_gateway.generate = AsyncMock()

    async def mock_generate(request: AIRequest) -> AIResponse:
        content = "[]"
        if request.system_instruction and "fact extractor" in request.system_instruction.lower():
            content = '[{"statement": "Test fact", "verbatim_quote": "Test content", "confidence": "HIGH", "is_inferred": false}]'
        return AIResponse(content=content, provider="mock", model="mock", is_structured=True)

    mock_gateway.generate.side_effect = mock_generate

    from app.services.extraction_service import ExtractionService

    async def override_get_extraction_service() -> ExtractionService:
        return ExtractionService(ai_gateway=mock_gateway, session=in_memory_db_session)

    from app.api.v1.endpoints.extraction import get_extraction_service

    test_app.dependency_overrides[get_extraction_service] = override_get_extraction_service

    # 2. Make API Request
    response = await async_client.post(f"/api/v1/extraction/chunks/{test_chunk.id}/extract")

    assert response.status_code == 200
    data = response.json()

    assert data["document_id"] == str(test_chunk.document_id)
    assert len(data["facts"]) == 1
    assert data["facts"][0]["statement"] == "Test fact"
    assert data["facts"][0]["provenance"]["chunk_id"] == str(test_chunk.id)

    assert "raw_extraction_metadata" in data
    assert len(data["raw_extraction_metadata"]["entities"]) == 0

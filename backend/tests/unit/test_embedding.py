"""Unit tests for embedding service."""

import asyncio
import uuid
from typing import Any

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.ai.embeddings.mock import MockEmbeddingProvider
from app.models.document import DocumentChunk
from app.services.embedding_service import EmbeddingService


@pytest.fixture
def mock_provider():
    return MockEmbeddingProvider(dimensions=10)


@pytest.mark.asyncio
async def test_embed_chunks(in_memory_db_session: AsyncSession, mock_provider: MockEmbeddingProvider):
    # We create some fake chunks
    # Since DocumentChunk has a relationship, we should just mock the objects or insert them.
    # It's a unit test, but since we pass session, we could use detached objects.
    service = EmbeddingService(in_memory_db_session, mock_provider)
    
    chunks = [
        DocumentChunk(id=uuid.uuid4(), document_id=uuid.uuid4(), content=f"content {i}", chunk_index=i, structural_type="PARAGRAPH")
        for i in range(5)
    ]
    
    await service.embed_chunks(chunks, batch_size=2, concurrency=2)
    
    for chunk in chunks:
        assert chunk.embedding is not None
        assert len(chunk.embedding) == 10
        assert chunk.embedding_metadata is not None
        assert chunk.embedding_metadata["provider"] == "mock"
        assert chunk.embedding_metadata["dimensions"] == 10


@pytest.mark.asyncio
async def test_embed_document(in_memory_db_session: AsyncSession, mock_provider: MockEmbeddingProvider):
    # Create tenant and document
    from app.models.tenant import Tenant
    from app.models.document import Document, DocumentChunk
    
    tenant = Tenant(id=uuid.uuid4(), name="Test Tenant")
    doc = Document(
        id=uuid.uuid4(), 
        tenant_id=tenant.id, 
        title="Test", 
        processing_status="COMPLETED",
        source_type="txt",
        sha256_hash="dummyhash",
    )
    chunk = DocumentChunk(
        document_id=doc.id,
        content="New chunk without embedding",
        chunk_index=99,
        structural_type="PARAGRAPH",
        embedding=None,
    )
    in_memory_db_session.add(tenant)
    in_memory_db_session.add(doc)
    in_memory_db_session.add(chunk)
    await in_memory_db_session.commit()
    
    # Let's query it back
    from sqlalchemy import select
    stmt = select(DocumentChunk).where(DocumentChunk.document_id == doc.id)
    retrieved_chunk = (await in_memory_db_session.scalars(stmt)).first()
    assert retrieved_chunk is not None
    assert retrieved_chunk.embedding is None
    
    service = EmbeddingService(in_memory_db_session, mock_provider)
    count = await service.embed_document(doc.id)
    assert count == 1

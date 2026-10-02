"""Integration tests for RAG engine and retrieval."""
import json
import uuid
from typing import Any

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.ai.embeddings.mock import MockEmbeddingProvider
from app.core.ai.gateway import AIGateway
from app.core.ai.models import AIRequest, AIResponse
from app.models.document import Document, DocumentChunk
from app.models.tenant import Tenant
from app.repositories.retrieval import KeywordRetriever
from app.schemas.retrieval import RetrievalQuery
from app.services.rag_service import RAGService


@pytest_asyncio.fixture
async def setup_rag_data(in_memory_db_session: AsyncSession) -> dict[str, Any]:
    tenant1 = Tenant(id=uuid.uuid4(), name="Tenant 1")
    tenant2 = Tenant(id=uuid.uuid4(), name="Tenant 2")
    in_memory_db_session.add_all([tenant1, tenant2])

    doc1 = Document(
        id=uuid.uuid4(), tenant_id=tenant1.id, title="Doc 1",
        source_type="md", sha256_hash="hash1"
    )
    doc2 = Document(
        id=uuid.uuid4(), tenant_id=tenant1.id, title="Doc 2",
        source_type="md", sha256_hash="hash2"
    )
    doc_t2 = Document(
        id=uuid.uuid4(), tenant_id=tenant2.id, title="Doc T2",
        source_type="md", sha256_hash="hash3"
    )
    in_memory_db_session.add_all([doc1, doc2, doc_t2])
    await in_memory_db_session.commit()

    provider = MockEmbeddingProvider()

    # We will manually set mock embeddings to control distance
    # For a deterministic vector retrieval, we'll assign vectors directly in the test later
    # For now, just generate random ones
    chunk1 = DocumentChunk(
        id=uuid.uuid4(), document_id=doc1.id, chunk_index=0,
        content="Registration closes October 8 at 5 PM.",
        source_location={}, embedding=await provider.embed_text("Registration closes October 8 at 5 PM.")
    )
    chunk2 = DocumentChunk(
        id=uuid.uuid4(), document_id=doc1.id, chunk_index=1,
        content="The server is experiencing downtime.",
        source_location={}, embedding=await provider.embed_text("The server is experiencing downtime.")
    )
    chunk3 = DocumentChunk(
        id=uuid.uuid4(), document_id=doc2.id, chunk_index=0,
        content="Duplicate info: Registration closes October 8.",
        source_location={}, embedding=await provider.embed_text("Duplicate info: Registration closes October 8.")
    )
    chunk_t2 = DocumentChunk(
        id=uuid.uuid4(), document_id=doc_t2.id, chunk_index=0,
        content="Tenant 2 secret: Project alpha launch is tomorrow.",
        source_location={}, embedding=await provider.embed_text("Tenant 2 secret: Project alpha launch is tomorrow.")
    )

    in_memory_db_session.add_all([chunk1, chunk2, chunk3, chunk_t2])
    await in_memory_db_session.commit()

    return {
        "tenant1": tenant1,
        "tenant2": tenant2,
        "doc1": doc1,
        "doc2": doc2,
        "chunk1": chunk1,
        "chunk2": chunk2,
        "chunk3": chunk3,
        "chunk_t2": chunk_t2,
        "provider": provider
    }


@pytest.mark.asyncio
@pytest.mark.integration
async def test_keyword_retriever(in_memory_db_session: AsyncSession, setup_rag_data: dict[str, Any]) -> None:
    t1 = setup_rag_data["tenant1"]
    chunk1 = setup_rag_data["chunk1"]

    retriever = KeywordRetriever(in_memory_db_session)
    query = RetrievalQuery(
        query="Registration closes",
        tenant_id=t1.id,
        top_k=5
    )
    results = await retriever.retrieve(query)

    assert len(results) >= 1
    # Keyword search will find chunk1 and chunk3
    contents = [r.content for r in results]
    assert any("Registration closes October 8" in c for c in contents)


@pytest.mark.asyncio
@pytest.mark.integration
async def test_tenant_isolation(in_memory_db_session: AsyncSession, setup_rag_data: dict[str, Any]) -> None:
    t1 = setup_rag_data["tenant1"]
    chunk_t2 = setup_rag_data["chunk_t2"]

    retriever = KeywordRetriever(in_memory_db_session)
    query = RetrievalQuery(
        query="Project alpha",
        tenant_id=t1.id, # Querying as T1
        top_k=5
    )
    results = await retriever.retrieve(query)

    # Should not find T2's document
    assert len(results) == 0


@pytest.mark.asyncio
@pytest.mark.integration
async def test_rag_citation_validation_and_hallucination(in_memory_db_session: AsyncSession, setup_rag_data: dict[str, Any]) -> None:
    # Test RAG service mock
    t1 = setup_rag_data["tenant1"]
    chunk1 = setup_rag_data["chunk1"]
    doc1 = setup_rag_data["doc1"]

    from unittest.mock import AsyncMock, MagicMock
    mock_gateway = MagicMock(spec=AIGateway)
    mock_gateway.generate = AsyncMock()

    # Return a hallucinated citation (bad chunk_id)
    bad_chunk_id = str(uuid.uuid4())
    async def mock_generate(request: AIRequest) -> AIResponse:
        content = json.dumps({
            "answer": "Registration closes October 15.", # hallucination
            "status": "SUCCESS",
            "citations": [
                {"document_id": str(doc1.id), "chunk_id": bad_chunk_id},
                {"document_id": str(doc1.id), "chunk_id": str(chunk1.id)} # valid one
            ]
        })
        return AIResponse(content=content, provider="mock", model="mock", is_structured=True)

    mock_gateway.generate.side_effect = mock_generate

    retriever = KeywordRetriever(in_memory_db_session)
    rag_service = RAGService(ai_gateway=mock_gateway, retriever=retriever)

    query = RetrievalQuery(
        query="registration closes",
        tenant_id=t1.id,
        top_k=2
    )

    output = await rag_service.answer_query(query)

    # The bad citation should be stripped out!
    assert len(output.citations) == 1
    assert output.citations[0].chunk_id == str(chunk1.id)
    assert output.answer == "Registration closes October 15."

@pytest.mark.asyncio
async def test_vector_retriever(in_memory_db_session: AsyncSession, setup_rag_data: dict[str, Any]) -> None:
    t1 = setup_rag_data["tenant1"]
    
    from app.core.ai.embeddings.mock import MockEmbeddingProvider
    provider = MockEmbeddingProvider()
    from app.repositories.retrieval import VectorRetriever
    retriever = VectorRetriever(in_memory_db_session, provider)
    
    query = RetrievalQuery(
        tenant_id=t1.id,
        query="important finding",
        top_k=2
    )
    
    results = await retriever.retrieve(query)
    # The VectorRetriever relies on SQLite degrading (is_postgres = False).
    # Since it's sqlite in test, it will return an empty list because vector search isn't supported in sqlite.
    assert isinstance(results, list)
    assert len(results) == 0


@pytest.mark.asyncio
async def test_hybrid_retriever(in_memory_db_session: AsyncSession, setup_rag_data: dict[str, Any]) -> None:
    t1 = setup_rag_data["tenant1"]
    
    from app.core.ai.embeddings.mock import MockEmbeddingProvider
    provider = MockEmbeddingProvider()
    from app.repositories.retrieval import HybridRetriever
    retriever = HybridRetriever(in_memory_db_session, provider)
    
    query = RetrievalQuery(
        tenant_id=t1.id,
        query="Registration closes",
        top_k=2,
        alpha=0.5
    )
    
    results = await retriever.retrieve(query)
    
    # Hybrid retriever merges Keyword + Vector results. Vector gives [], Keyword gives matches.
    assert len(results) > 0
    assert results[0].retrieval_method == "HYBRID"
    assert results[0].retrieval_score <= 0.5  # Since it's halved by alpha

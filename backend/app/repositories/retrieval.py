"""Database retrieval implementations for Context Engine."""
import uuid
from abc import ABC, abstractmethod

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.ai.embeddings.base import EmbeddingProvider
from app.models.document import DocumentChunk
from app.schemas.retrieval import RetrievalQuery, RetrievalResult


class BaseRetriever(ABC):
    """Abstract retrieval engine interface."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    @abstractmethod
    async def retrieve(self, query: RetrievalQuery) -> list[RetrievalResult]:
        """Execute a retrieval query against the database."""
        pass


class VectorRetriever(BaseRetriever):
    """Semantic vector search using pgvector."""

    def __init__(self, session: AsyncSession, embedding_provider: EmbeddingProvider) -> None:
        super().__init__(session)
        self.provider = embedding_provider

    async def retrieve(self, query: RetrievalQuery) -> list[RetrievalResult]:
        # 1. Embed query
        query_vector = await self.provider.embed_text(query.query)

        # 2. Build base query with Tenant isolation
        stmt = select(DocumentChunk).join(DocumentChunk.document).where(
            DocumentChunk.document.has(tenant_id=query.tenant_id)
        )

        # 3. Document scope filter
        if query.document_ids:
            stmt = stmt.where(DocumentChunk.document_id.in_(query.document_ids))

        # 4. Filter out chunks without embeddings
        stmt = stmt.where(DocumentChunk.embedding.is_not(None))

        # We need to perform vector distance. SQLite does not support this.
        # So we'll use raw text if postgres dialect, otherwise we simulate it?
        # Actually, SQLAlchemy with pgvector supports .cosine_distance().
        # But we need to check if the dialect is postgresql, else degrade gracefully or throw error.

        bind = self.session.bind
        is_postgres = bind and bind.dialect.name == "postgresql"

        results = []
        if is_postgres:
            # PostgreSQL pgvector similarity
            stmt = stmt.order_by(DocumentChunk.embedding.cosine_distance(query_vector))
            stmt = stmt.limit(query.top_k)

            (await self.session.scalars(stmt)).all()

            # Reconstruct scores (1 - cosine_distance is cosine similarity)
            # We can select the distance in the query, but for simplicity we'll just return it.
            # In a real query, we'd do `.add_columns(DocumentChunk.embedding.cosine_distance(...))`
            # Let's do that for accurate scores.
            stmt = select(DocumentChunk, DocumentChunk.embedding.cosine_distance(query_vector).label('distance'))
            stmt = stmt.join(DocumentChunk.document).where(
                DocumentChunk.document.has(tenant_id=query.tenant_id)
            )
            if query.document_ids:
                stmt = stmt.where(DocumentChunk.document_id.in_(query.document_ids))
            stmt = stmt.where(DocumentChunk.embedding.is_not(None))
            stmt = stmt.order_by(text("distance")).limit(query.top_k)

            rows = (await self.session.execute(stmt)).all()

            from typing import Any, cast
            for r in rows:
                row_tuple = cast(tuple[Any, Any], r)
                chunk = row_tuple[0]
                distance = row_tuple[1]
                score = 1.0 - (distance or 0.0)
                if score >= query.min_score:
                    results.append(RetrievalResult(
                        chunk_id=chunk.id,
                        document_id=chunk.document_id,
                        content=chunk.content,
                        source_location=chunk.source_location,
                        retrieval_method="VECTOR",
                        retrieval_score=score,
                    ))
        else:
            # Fallback for SQLite testing (no vector similarity possible, return empty or mock)
            pass

        return results


class KeywordRetriever(BaseRetriever):
    """Exact keyword / simple full-text search fallback."""

    async def retrieve(self, query: RetrievalQuery) -> list[RetrievalResult]:
        # For simplicity, we just do a naive ILIKE search splitting on spaces.
        # In a real PostgreSQL app, this would use `to_tsvector`.
        terms = query.query.split()

        stmt = select(DocumentChunk).join(DocumentChunk.document).where(
            DocumentChunk.document.has(tenant_id=query.tenant_id)
        )

        if query.document_ids:
            stmt = stmt.where(DocumentChunk.document_id.in_(query.document_ids))

        # Basic keyword match on content
        for term in terms:
            if len(term) > 3: # Ignore stop words length loosely
                stmt = stmt.where(DocumentChunk.content.ilike(f"%{term}%"))

        stmt = stmt.limit(query.top_k)

        chunks = (await self.session.scalars(stmt)).all()

        results = []
        for chunk in chunks:
            # Dummy score for ILIKE
            score = 0.5
            if score >= query.min_score:
                results.append(RetrievalResult(
                    chunk_id=chunk.id,
                    document_id=chunk.document_id,
                    content=chunk.content,
                    source_location=chunk.source_location,
                    retrieval_method="KEYWORD",
                    retrieval_score=score,
                ))

        return results


class HybridRetriever(BaseRetriever):
    """Fuses Vector and Keyword search using Reciprocal Rank Fusion (RRF) or simple score weighting."""

    def __init__(self, session: AsyncSession, embedding_provider: EmbeddingProvider) -> None:
        super().__init__(session)
        self.vector_retriever = VectorRetriever(session, embedding_provider)
        self.keyword_retriever = KeywordRetriever(session)

    async def retrieve(self, query: RetrievalQuery) -> list[RetrievalResult]:
        # We can run them in parallel
        import asyncio
        vector_task = asyncio.create_task(self.vector_retriever.retrieve(query))
        keyword_task = asyncio.create_task(self.keyword_retriever.retrieve(query))

        vector_results, keyword_results = await asyncio.gather(vector_task, keyword_task)

        # Merge results using a basic linear combination
        merged: dict[uuid.UUID, RetrievalResult] = {}

        # Alpha is weight of vector, 1-alpha is weight of keyword
        # E.g. alpha = 0.7 means 70% vector score, 30% keyword score

        for r in vector_results:
            merged[r.chunk_id] = r
            merged[r.chunk_id].retrieval_score *= query.alpha
            merged[r.chunk_id].retrieval_method = "HYBRID"

        for r in keyword_results:
            if r.chunk_id in merged:
                merged[r.chunk_id].retrieval_score += (r.retrieval_score * (1.0 - query.alpha))
            else:
                r.retrieval_score *= (1.0 - query.alpha)
                r.retrieval_method = "HYBRID"
                merged[r.chunk_id] = r

        # Sort and take top_k
        sorted_results = sorted(merged.values(), key=lambda x: x.retrieval_score, reverse=True)

        # Filter by min score
        final_results = [r for r in sorted_results if r.retrieval_score >= query.min_score]

        return final_results[:query.top_k]

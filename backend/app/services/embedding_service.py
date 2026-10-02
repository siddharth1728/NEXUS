"""Service for generating and persisting embeddings."""
import asyncio
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.ai.embeddings.base import EmbeddingProvider
from app.models.document import DocumentChunk


class EmbeddingService:
    """Orchestrates document chunk embedding generation and persistence."""

    def __init__(self, session: AsyncSession, provider: EmbeddingProvider) -> None:
        self.session = session
        self.provider = provider

    async def embed_chunks(
        self, chunks: list[DocumentChunk], batch_size: int = 100, concurrency: int = 3
    ) -> None:
        """
        Generates and saves embeddings for a list of chunks, in bounded batches.
        Idempotent: Replaces existing embeddings.
        """
        semaphore = asyncio.Semaphore(concurrency)

        async def embed_batch(batch: list[DocumentChunk]) -> None:
            async with semaphore:
                texts = [chunk.content for chunk in batch]
                # Fallback to single generation if batch fails or is not implemented optimally
                vectors = await self.provider.embed_texts(texts)

                for chunk, vector in zip(batch, vectors, strict=False):
                    chunk.embedding = vector
                    chunk.embedding_metadata = {
                        "provider": self.provider.provider_name,
                        "model": self.provider.model_name,
                        "dimensions": self.provider.dimensions,
                    }
                    self.session.add(chunk)

        # Batching logic
        batches = [chunks[i : i + batch_size] for i in range(0, len(chunks), batch_size)]

        tasks = [asyncio.create_task(embed_batch(batch)) for batch in batches]
        await asyncio.gather(*tasks)

        # Note: Caller is responsible for committing the session

    async def embed_document(self, document_id: Any, batch_size: int = 100, concurrency: int = 3) -> int:
        """Finds all chunks for a document without embeddings and embeds them."""
        stmt = select(DocumentChunk).where(
            DocumentChunk.document_id == document_id,
            DocumentChunk.embedding.is_(None)
        )
        chunks = (await self.session.scalars(stmt)).all()

        if not chunks:
            return 0

        await self.embed_chunks(list(chunks), batch_size=batch_size, concurrency=concurrency)
        return len(chunks)

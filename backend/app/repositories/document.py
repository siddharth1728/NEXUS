"""Document and ExtractionJob Repositories."""

import uuid

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.models.document import Document, DocumentChunk, ExtractionJob
from app.repositories.base import BaseRepository


class DocumentRepository(BaseRepository[Document]):
    """Repository for Document persistence operations."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(Document, session)

    async def get_document_for_tenant(
        self, document_id: uuid.UUID, tenant_id: uuid.UUID
    ) -> Document | None:
        """Fetch a document strictly scoped to a tenant."""
        stmt = select(Document).where(Document.id == document_id, Document.tenant_id == tenant_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_for_tenant(
        self, tenant_id: uuid.UUID, offset: int = 0, limit: int = 50
    ) -> list[Document]:
        """List documents scoped to a tenant."""
        stmt = select(Document).where(Document.tenant_id == tenant_id).offset(offset).limit(limit)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())


class ExtractionJobRepository(BaseRepository[ExtractionJob]):
    """Repository for ExtractionJob persistence operations."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(ExtractionJob, session)

    async def get_job_with_document(self, job_id: uuid.UUID) -> ExtractionJob | None:
        """Fetch an extraction job, assuming we might need to join/check document later."""
        stmt = select(ExtractionJob).where(ExtractionJob.id == job_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()


class DocumentChunkRepository(BaseRepository[DocumentChunk]):
    """Repository for DocumentChunk persistence operations."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(DocumentChunk, session)

    async def list_for_document(
        self, document_id: uuid.UUID, offset: int = 0, limit: int = 1000
    ) -> list[DocumentChunk]:
        """List chunks for a specific document, ordered by chunk_index."""
        stmt = (
            select(DocumentChunk)
            .where(DocumentChunk.document_id == document_id)
            .order_by(DocumentChunk.chunk_index.asc())
            .offset(offset)
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

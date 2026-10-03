"""Document and ExtractionJob Service."""

import uuid
from pathlib import Path

from fastapi import UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.document import SimpleTextParser, compute_file_hash
from app.core.errors import AppError, ConflictError, NotFoundError
from app.core.storage import get_storage_provider
from app.models.document import Document, DocumentChunk, ExtractionJob
from app.models.enums import ExtractionJobStatus
from app.repositories.document import (
    DocumentChunkRepository,
    DocumentRepository,
    ExtractionJobRepository,
)
from app.schemas.document import DocumentCreate, ExtractionJobCreate

VALID_JOB_TRANSITIONS = {
    ExtractionJobStatus.PENDING: {ExtractionJobStatus.RUNNING},
    ExtractionJobStatus.RUNNING: {ExtractionJobStatus.COMPLETED, ExtractionJobStatus.FAILED},
    ExtractionJobStatus.FAILED: {ExtractionJobStatus.RETRYING},
    ExtractionJobStatus.RETRYING: {ExtractionJobStatus.RUNNING},
}


class UnsupportedFormatError(AppError):
    status_code = 400
    error_code = "UNSUPPORTED_FORMAT"


class DocumentService:
    """Application use-case service for Document and ExtractionJob management."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.doc_repo = DocumentRepository(session)
        self.job_repo = ExtractionJobRepository(session)
        self.chunk_repo = DocumentChunkRepository(session)
        self.storage = get_storage_provider()
        self.parser = SimpleTextParser()

    async def create_document(
        self, tenant_id: uuid.UUID, owner_id: uuid.UUID | None, data: DocumentCreate
    ) -> Document:
        """Create a new document."""
        doc = Document(
            tenant_id=tenant_id,
            owner_id=owner_id,
            title=data.title,
            source_type=data.source_type,
            source_uri=data.source_uri,
            sha256_hash=data.sha256_hash,
            raw_metadata=data.raw_metadata,
            processing_status="PENDING",
        )
        return await self.doc_repo.create(doc)

    async def list_documents(
        self, tenant_id: uuid.UUID, offset: int = 0, limit: int = 50
    ) -> list[Document]:
        """List documents scoped to a tenant."""
        return await self.doc_repo.list_for_tenant(tenant_id, offset, limit)

    async def get_document(self, document_id: uuid.UUID, tenant_id: uuid.UUID) -> Document:
        """Get a document with strict tenant isolation."""
        doc = await self.doc_repo.get_document_for_tenant(document_id, tenant_id)
        if not doc:
            raise NotFoundError("Document", str(document_id))
        return doc

    async def create_extraction_job(
        self, tenant_id: uuid.UUID, data: ExtractionJobCreate
    ) -> ExtractionJob:
        """Create a new extraction job for a document, ensuring tenant authorization."""
        await self.get_document(data.document_id, tenant_id)  # Enforce tenant isolation

        job = ExtractionJob(
            document_id=data.document_id,
            status=ExtractionJobStatus.PENDING,
            retry_count=0,
        )
        return await self.job_repo.create(job)

    async def get_extraction_job(self, job_id: uuid.UUID, tenant_id: uuid.UUID) -> ExtractionJob:
        """Get an extraction job, enforcing tenant isolation via its parent document."""
        job = await self.job_repo.get_job_with_document(job_id)
        if not job:
            raise NotFoundError("ExtractionJob", str(job_id))

        # Validate tenant isolation via parent document (which is preloaded by relation if lazy="joined" or we can explicit fetch)
        # For safety and explicit boundaries without assuming ORM loading strategy:
        await self.get_document(job.document_id, tenant_id)

        return job

    async def transition_job_state(
        self,
        job_id: uuid.UUID,
        tenant_id: uuid.UUID,
        new_status: ExtractionJobStatus,
        error_category: str | None = None,
    ) -> ExtractionJob:
        """Transition job state, enforcing valid state machine rules."""
        job = await self.get_extraction_job(job_id, tenant_id)

        if job.status == new_status:
            return job

        valid_next_states = VALID_JOB_TRANSITIONS.get(job.status, set())
        if new_status not in valid_next_states:
            raise ConflictError(f"Invalid transition from {job.status} to {new_status}")

        job.status = new_status
        if error_category and new_status == ExtractionJobStatus.FAILED:
            job.error_category = error_category

        if new_status == ExtractionJobStatus.RETRYING:
            job.retry_count += 1

        await self.session.flush()
        return job

    async def ingest_file(
        self, tenant_id: uuid.UUID, file: UploadFile, owner_id: uuid.UUID | None = None
    ) -> Document:
        """Complete ingestion pipeline: Validate, Store, Parse, Chunk, Persist."""
        # 1. Validation
        ext = Path(file.filename or "").suffix.lower()
        if ext not in self.parser.supported_extensions:
            raise UnsupportedFormatError(
                f"Unsupported format {ext}. Supported: {self.parser.supported_extensions}"
            )

        # 2. Store File
        storage_uri = await self.storage.store_file(file, tenant_id)

        # 3. Hash & Identity
        file_path = await self.storage.get_file_path(storage_uri)
        file_hash = compute_file_hash(file_path)

        # 4. Create Document Record
        doc_data = DocumentCreate(
            title=file.filename or "Untitled",
            source_type=ext.lstrip("."),
            source_uri=storage_uri,
            sha256_hash=file_hash,
            raw_metadata={"content_type": file.content_type, "size": file.size},
        )
        doc = await self.create_document(tenant_id, owner_id, doc_data)

        # 5. Create Extraction Job
        job = await self.create_extraction_job(tenant_id, ExtractionJobCreate(document_id=doc.id))

        # 6. Parse and Chunk
        try:
            await self.transition_job_state(job.id, tenant_id, ExtractionJobStatus.RUNNING)
            parsed_doc = await self.parser.parse(file_path, file.content_type)

            # 7. Persist Chunks
            for chunk_data in parsed_doc.chunks:
                chunk = DocumentChunk(
                    document_id=doc.id,
                    chunk_index=chunk_data.chunk_index,
                    content=chunk_data.content,
                    structural_type=chunk_data.structural_type,
                    source_location=chunk_data.source_location.model_dump(exclude_none=True),
                    chunk_metadata=chunk_data.metadata,
                )
                self.session.add(chunk)

            doc.processing_status = "COMPLETED"
            await self.transition_job_state(job.id, tenant_id, ExtractionJobStatus.COMPLETED)

        except Exception as e:
            # Handle partial or total failure
            doc.processing_status = "FAILED"
            await self.transition_job_state(
                job.id, tenant_id, ExtractionJobStatus.FAILED, error_category=str(e)
            )
            raise AppError(f"Failed to process document: {str(e)}") from e

        return doc

    async def get_document_chunks(
        self, document_id: uuid.UUID, tenant_id: uuid.UUID, offset: int = 0, limit: int = 1000
    ) -> tuple[list[DocumentChunk], int]:
        """Get parsed chunks for a document, ensuring tenant isolation."""
        # Enforce tenant check
        await self.get_document(document_id, tenant_id)
        chunks = await self.chunk_repo.list_for_document(document_id, offset, limit)
        total = await self.chunk_repo.count({"document_id": document_id})
        return chunks, total

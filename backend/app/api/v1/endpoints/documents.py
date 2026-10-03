"""Document and ExtractionJob Endpoints."""

import uuid

import fastapi
from fastapi import APIRouter, Depends, File, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_tenant_id, get_db_session
from app.schemas.document import (
    DocumentChunkResponse,
    DocumentCreate,
    DocumentResponse,
    ExtractionJobCreate,
    ExtractionJobResponse,
    ExtractionJobStateTransition,
)
from app.services.document_service import DocumentService

router = APIRouter()


def get_document_service(session: AsyncSession = Depends(get_db_session)) -> DocumentService:
    return DocumentService(session)


@router.post("/upload", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(
    file: UploadFile = File(...),
    tenant_id: uuid.UUID = Depends(get_current_tenant_id),
    service: DocumentService = Depends(get_document_service),
) -> DocumentResponse:
    """Upload and ingest a document."""
    doc = await service.ingest_file(tenant_id, file, owner_id=None)
    await service.session.commit()
    return DocumentResponse.model_validate(doc)


@router.post("", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
async def create_document(
    data: DocumentCreate,
    tenant_id: uuid.UUID = Depends(get_current_tenant_id),
    service: DocumentService = Depends(get_document_service),
) -> DocumentResponse:
    """Create a new document."""
    # Temporarily hardcoding owner_id as null, can be expanded to get_current_user_id
    doc = await service.create_document(tenant_id, owner_id=None, data=data)
    await service.session.commit()
    return DocumentResponse.model_validate(doc)


@router.get("", response_model=list[DocumentResponse])
@router.get("/", response_model=list[DocumentResponse], include_in_schema=False)
async def list_documents(
    offset: int = 0,
    limit: int = 50,
    tenant_id: uuid.UUID = Depends(get_current_tenant_id),
    service: DocumentService = Depends(get_document_service),
) -> list[DocumentResponse]:
    """List documents for the current tenant."""
    docs = await service.list_documents(tenant_id, offset=offset, limit=limit)
    return [DocumentResponse.model_validate(doc) for doc in docs]


@router.get("/{document_id}", response_model=DocumentResponse)
async def get_document(
    document_id: uuid.UUID,
    tenant_id: uuid.UUID = Depends(get_current_tenant_id),
    service: DocumentService = Depends(get_document_service),
) -> DocumentResponse:
    """Get a specific document by ID."""
    doc = await service.get_document(document_id, tenant_id)
    return DocumentResponse.model_validate(doc)


@router.post("/jobs", response_model=ExtractionJobResponse, status_code=status.HTTP_201_CREATED)
async def create_extraction_job(
    data: ExtractionJobCreate,
    tenant_id: uuid.UUID = Depends(get_current_tenant_id),
    service: DocumentService = Depends(get_document_service),
) -> ExtractionJobResponse:
    """Request a new extraction job for a document."""
    job = await service.create_extraction_job(tenant_id, data)
    await service.session.commit()
    return ExtractionJobResponse.model_validate(job)


@router.get("/jobs/{job_id}", response_model=ExtractionJobResponse)
async def get_extraction_job(
    job_id: uuid.UUID,
    tenant_id: uuid.UUID = Depends(get_current_tenant_id),
    service: DocumentService = Depends(get_document_service),
) -> ExtractionJobResponse:
    """Get an extraction job by ID."""
    job = await service.get_extraction_job(job_id, tenant_id)
    return ExtractionJobResponse.model_validate(job)


@router.post("/jobs/{job_id}/transition", response_model=ExtractionJobResponse)
async def transition_extraction_job(
    job_id: uuid.UUID,
    data: ExtractionJobStateTransition,
    tenant_id: uuid.UUID = Depends(get_current_tenant_id),
    service: DocumentService = Depends(get_document_service),
) -> ExtractionJobResponse:
    """Transition an extraction job's state."""
    job = await service.transition_job_state(
        job_id, tenant_id, data.new_status, data.error_category
    )
    await service.session.commit()
    return ExtractionJobResponse.model_validate(job)


@router.get("/{document_id}/chunks", response_model=list[DocumentChunkResponse])
async def get_document_chunks(
    document_id: uuid.UUID,
    response: fastapi.Response,
    offset: int = 0,
    limit: int = 1000,
    tenant_id: uuid.UUID = Depends(get_current_tenant_id),
    service: DocumentService = Depends(get_document_service),
) -> list[DocumentChunkResponse]:
    """Get parsed chunks for a document."""
    chunks, total = await service.get_document_chunks(document_id, tenant_id, offset, limit)
    response.headers["X-Total-Count"] = str(total)
    response.headers["X-Total-Pages"] = str((total + limit - 1) // limit if limit > 0 else 1)
    response.headers["X-Current-Page"] = str((offset // limit) + 1 if limit > 0 else 1)
    response.headers["X-Per-Page"] = str(limit)
    return [DocumentChunkResponse.model_validate(chunk) for chunk in chunks]

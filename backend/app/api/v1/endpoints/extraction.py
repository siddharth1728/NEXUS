"""NEXUS API Endpoints for AI Extraction."""

import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select

from app.api.deps import get_current_tenant_id, get_db_session
from app.core.ai.gateway import AIGateway
from app.models.document import DocumentChunk
from app.schemas.extraction import ChunkExtractionOutput, ExtractedFactResponse, ProvenanceSchema
from app.services.extraction_service import ExtractionService

router = APIRouter()


async def get_extraction_service(session: Any = Depends(get_db_session)) -> ExtractionService:
    return ExtractionService(ai_gateway=AIGateway(), session=session)


@router.post(
    "/chunks/{chunk_id}/extract",
    response_model=dict,
    status_code=status.HTTP_200_OK,
)
async def extract_chunk_information(
    chunk_id: uuid.UUID,
    tenant_id: uuid.UUID = Depends(get_current_tenant_id),
    service: ExtractionService = Depends(get_extraction_service),
) -> dict:
    """
    Runs the full AI extraction pipeline on a specific document chunk.
    """

    # 1. Fetch the chunk and verify tenant access
    stmt = select(DocumentChunk).where(DocumentChunk.id == chunk_id)
    result = await service.session.execute(stmt)
    chunk = result.scalar_one_or_none()

    if not chunk:
        raise HTTPException(status_code=404, detail="Chunk not found.")

    # We must explicitly authorize via the parent document's tenant_id to prevent cross-tenant extraction
    # Since SQLAlchemy relationships might be lazy, we should explicitly join or just load it
    await service.session.refresh(chunk, ["document"])
    if chunk.document.tenant_id != tenant_id:
        raise HTTPException(status_code=403, detail="Not authorized to access this chunk.")

    # 2. Run extraction
    output: ChunkExtractionOutput = await service.extract_chunk(chunk)

    # 3. Persist facts
    facts = await service.persist_extracted_facts(
        tenant_id=tenant_id, document_id=chunk.document_id, chunk_id=chunk.id, output=output
    )

    await service.session.commit()

    # 4. Format response
    provenance = ProvenanceSchema(
        document_id=chunk.document_id,
        chunk_id=chunk.id,
        chunk_index=chunk.chunk_index,
        source_location=chunk.source_location,
    )

    formatted_facts = []
    for fact in facts:
        formatted_facts.append(
            ExtractedFactResponse(
                id=fact.id,
                statement=fact.statement,
                verbatim_quote=fact.verbatim_quote,
                confidence=fact.confidence,
                metadata=fact.metadata_,
                provenance=provenance,
            )
        )

    return {
        "document_id": chunk.document_id,
        "facts": [f.model_dump(by_alias=True) for f in formatted_facts],
        "raw_extraction_metadata": {
            "entities": [e.model_dump() for e in output.entities],
            "temporal_items": [t.model_dump() for t in output.temporal_items],
            "requirements": [r.model_dump() for r in output.requirements],
            "candidate_actions": [c.model_dump() for c in output.candidate_actions],
        },
    }

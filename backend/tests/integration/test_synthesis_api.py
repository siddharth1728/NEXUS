"""Integration tests for Action Synthesis API Phase 02A."""

import uuid

import pytest
from httpx import AsyncClient

from app.models.enums import ActionStatus

TEST_TENANT_ID = uuid.UUID("00000000-0000-4000-8000-000000000001")


@pytest.mark.asyncio
async def test_synthesize_endpoint(async_client: AsyncClient, test_app) -> None:  # type: ignore
    from unittest.mock import AsyncMock

    from app.api.v1.endpoints.synthesis import get_synthesis_service
    from app.schemas.synthesis import SynthesisResult
    from app.services.synthesis_service import SynthesisService

    async def override_get_synthesis_service():  # type: ignore
        mock_service = AsyncMock(spec=SynthesisService)
        mock_service.synthesize.return_value = SynthesisResult(
            candidates=[],
            processing_time_ms=10,
            llm_usage={}
        )
        return mock_service

    test_app.dependency_overrides[get_synthesis_service] = override_get_synthesis_service

    context = {
        "tenant_id": str(TEST_TENANT_ID),
        "facts": [{"statement": "Submit forms by Oct 8", "verbatim_quote": "Submit forms by Oct 8", "confidence": "HIGH", "is_inferred": False}],
        "entities": [],
        "temporal_items": [],
        "requirements": [],
        "candidate_actions": [],
        "rag_context": [],
        "personalization_context": {},
        "conflict_information": [],
        "dependency_information": []
    }

    response = await async_client.post(
        "/api/v1/synthesis/synthesize",
        json=context,
        headers={"X-Tenant-ID": str(TEST_TENANT_ID)},
    )

    assert response.status_code == 200
    data = response.json()
    assert "candidates" in data

    test_app.dependency_overrides.pop(get_synthesis_service, None)


@pytest.mark.asyncio
async def test_validate_candidate_endpoint(async_client: AsyncClient, test_app) -> None:  # type: ignore
    from unittest.mock import AsyncMock

    from app.api.v1.endpoints.synthesis import get_synthesis_service
    from app.schemas.synthesis import CandidateActionValidationResult
    from app.services.synthesis_service import SynthesisService

    async def override_get_synthesis_service():  # type: ignore
        mock_service = AsyncMock(spec=SynthesisService)
        mock_service.validate_candidate.return_value = CandidateActionValidationResult(
            is_valid=True,
            status="APPROVED",
            validation_errors=[]
        )
        return mock_service

    test_app.dependency_overrides[get_synthesis_service] = override_get_synthesis_service

    candidate = {
        "title": "Submit Forms",
        "description": "Submit forms by Oct 8",
        "classification": "EXPLICIT",
        "confidence": "HIGH",
        "rationale": "Explicitly stated in fact.",
        "source_refs": [
            {
                "document_id": str(uuid.uuid4()),
                "chunk_id": str(uuid.uuid4())
            }
        ]
    }

    response = await async_client.post(
        "/api/v1/synthesis/validate",
        json=candidate,
        headers={"X-Tenant-ID": str(TEST_TENANT_ID)},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["is_valid"] is True
    assert data["status"] == "APPROVED"

    test_app.dependency_overrides.pop(get_synthesis_service, None)


@pytest.mark.asyncio
async def test_create_action_from_candidate_endpoint(async_client: AsyncClient, test_app) -> None:  # type: ignore
    from unittest.mock import AsyncMock

    from app.api.v1.endpoints.synthesis import get_synthesis_service
    from app.services.synthesis_service import SynthesisService

    # Override get_synthesis_service to mock create_action_from_candidate
    async def override_get_synthesis_service():  # type: ignore
        mock_service = AsyncMock(spec=SynthesisService)
        from datetime import UTC, datetime

        from app.schemas.action import ActionResponse
        mock_service.create_action_from_candidate.return_value = ActionResponse(
            id=uuid.uuid4(),
            tenant_id=TEST_TENANT_ID,
            title="Submit Forms Integration",
            description="Submit forms by Oct 8",
            status=ActionStatus.CANDIDATE,
            priority="P2",
            confidence="HIGH",  # type: ignore
            is_hard_deadline=False,
            source_document_id=uuid.uuid4(),
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC)
        )
        return mock_service

    test_app.dependency_overrides[get_synthesis_service] = override_get_synthesis_service

    candidate = {
        "title": "Submit Forms Integration",
        "description": "Submit forms by Oct 8",
        "classification": "EXPLICIT",
        "confidence": "HIGH",
        "rationale": "Explicitly stated in fact.",
        "source_refs": [
            {
                "document_id": str(uuid.uuid4()),
                "chunk_id": str(uuid.uuid4())
            }
        ]
    }

    response = await async_client.post(
        "/api/v1/synthesis/create-action",
        json=candidate,
        headers={"X-Tenant-ID": str(TEST_TENANT_ID)},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Submit Forms Integration"

    # Clean up override
    test_app.dependency_overrides.pop(get_synthesis_service, None)


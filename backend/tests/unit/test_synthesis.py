"""Unit tests for Action Synthesis Phase 02A."""

import uuid
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.models.enums import ConfidenceLevel
from app.schemas.synthesis import (
    CandidateAction,
    SynthesisContext,
)
from app.services.synthesis_service import SynthesisService


@pytest.fixture
def mock_ai_gateway():  # type: ignore
    return AsyncMock()

@pytest.fixture
def mock_action_service():  # type: ignore
    return AsyncMock()

@pytest.fixture
def synthesis_service(mock_ai_gateway, mock_action_service):  # type: ignore
    # Bypass file loading for unit tests
    service = SynthesisService(mock_ai_gateway, mock_action_service)
    service._load_prompt = lambda: "Test prompt"  # type: ignore
    return service


def create_candidate(**kwargs: Any) -> CandidateAction:
    defaults = {
        "title": "Test Task",
        "description": "Do the thing",
        "classification": "EXPLICIT",
        "confidence": ConfidenceLevel.HIGH,
        "rationale": "Because."
    }
    defaults.update(kwargs)
    return CandidateAction(**defaults)  # type: ignore


@pytest.mark.asyncio
async def test_validate_valid_candidate(synthesis_service: SynthesisService) -> None:
    tenant_id = str(uuid.uuid4())
    doc_id = uuid.uuid4()
    chunk_id = uuid.uuid4()

    candidate = create_candidate(
        source_refs=[{"document_id": doc_id, "chunk_id": chunk_id}]
    )

    result = await synthesis_service.validate_candidate(candidate, tenant_id)
    assert result.is_valid is True
    assert result.status == "APPROVED"


@pytest.mark.asyncio
async def test_validate_invalid_missing_source(synthesis_service: SynthesisService) -> None:
    tenant_id = str(uuid.uuid4())

    candidate = create_candidate(source_refs=[])

    result = await synthesis_service.validate_candidate(candidate, tenant_id)
    assert result.is_valid is False
    assert "Missing source references." in result.reasons


@pytest.mark.asyncio
async def test_validate_conflict(synthesis_service: SynthesisService) -> None:
    tenant_id = str(uuid.uuid4())
    doc_id = uuid.uuid4()
    chunk_id = uuid.uuid4()

    candidate = create_candidate(
        source_refs=[{"document_id": doc_id, "chunk_id": chunk_id}],
        confidence=ConfidenceLevel.CONFLICT
    )

    result = await synthesis_service.validate_candidate(candidate, tenant_id)
    assert result.is_valid is False
    assert "Conflict detected in sources." in result.reasons
    assert result.status == "REQUIRES_REVIEW"


@pytest.mark.asyncio
async def test_create_action_from_candidate_deduplication(synthesis_service, mock_action_service) -> None:  # type: ignore
    tenant_id = str(uuid.uuid4())
    doc_id = uuid.uuid4()
    chunk_id = uuid.uuid4()

    candidate = create_candidate(
        title="Duplicate Task",
        source_refs=[{"document_id": doc_id, "chunk_id": chunk_id}]
    )

    # Mock list_actions to return an existing action with the same title
    from datetime import UTC, datetime

    from app.models.action import Action, ActionStatus
    now = datetime.now(UTC)
    existing_mock = Action(
        id=uuid.uuid4(),
        tenant_id=uuid.UUID(tenant_id) if isinstance(tenant_id, str) else tenant_id,
        title="Duplicate Task",
        description="desc",
        status=ActionStatus.CANDIDATE,
        priority="P2",
        confidence=ConfidenceLevel.HIGH,
        is_hard_deadline=False,
        created_at=now,
        updated_at=now
    )
    mock_action_service.list_actions.return_value = ([existing_mock], 1)

    result = await synthesis_service.create_action_from_candidate(tenant_id, candidate)

    # It should return the existing action without calling create
    assert result.title == existing_mock.title
    mock_action_service.create_action.assert_not_called()


@pytest.mark.asyncio
async def test_create_action_from_candidate_new(synthesis_service, mock_action_service) -> None:  # type: ignore
    tenant_id = str(uuid.uuid4())
    doc_id = uuid.uuid4()
    chunk_id = uuid.uuid4()

    candidate = create_candidate(
        title="New Task",
        source_refs=[{"document_id": doc_id, "chunk_id": chunk_id}]
    )

    mock_action_service.list_actions.return_value = ([], 0)

    from datetime import UTC, datetime

    from app.models.action import Action, ActionStatus
    now = datetime.now(UTC)
    new_action_mock = Action(
        id=uuid.uuid4(),
        tenant_id=uuid.UUID(tenant_id) if isinstance(tenant_id, str) else tenant_id,
        title="New Task",
        description="desc",
        status=ActionStatus.CANDIDATE,
        priority="P2",
        confidence=ConfidenceLevel.HIGH,
        is_hard_deadline=False,
        created_at=now,
        updated_at=now
    )
    mock_action_service.create_action.return_value = new_action_mock

    result = await synthesis_service.create_action_from_candidate(tenant_id, candidate)

    assert result.title == new_action_mock.title
    mock_action_service.create_action.assert_called_once()

@pytest.mark.asyncio
async def test_synthesize_success(synthesis_service: SynthesisService, mock_ai_gateway) -> None:  # type: ignore
    tenant_id = uuid.uuid4()
    context = SynthesisContext(tenant_id=tenant_id)

    mock_response = MagicMock()
    mock_response.content = '{"candidates": [{"title": "Task 1", "description": "desc", "classification": "EXPLICIT", "confidence": "HIGH", "rationale": "rat"}]}'
    mock_ai_gateway.generate.return_value = mock_response

    result = await synthesis_service.synthesize(context)

    assert len(result.candidates) == 1
    assert result.candidates[0].title == "Task 1"

@pytest.mark.asyncio
async def test_synthesize_repair_loop(synthesis_service: SynthesisService, mock_ai_gateway) -> None:  # type: ignore
    tenant_id = uuid.uuid4()
    context = SynthesisContext(tenant_id=tenant_id)

    mock_resp_bad = MagicMock()
    mock_resp_bad.content = 'invalid json'

    mock_resp_good = MagicMock()
    mock_resp_good.content = '{"candidates": [{"title": "Task 1", "description": "desc", "classification": "EXPLICIT", "confidence": "HIGH", "rationale": "rat"}]}'

    mock_ai_gateway.generate.side_effect = [mock_resp_bad, mock_resp_good]

    result = await synthesis_service.synthesize(context, max_retries=1)

    assert len(result.candidates) == 1
    assert mock_ai_gateway.generate.call_count == 2

@pytest.mark.asyncio
async def test_synthesize_fail_max_retries(synthesis_service: SynthesisService, mock_ai_gateway) -> None:  # type: ignore
    tenant_id = uuid.uuid4()
    context = SynthesisContext(tenant_id=tenant_id)

    mock_resp_bad = MagicMock()
    mock_resp_bad.content = 'invalid json'

    mock_ai_gateway.generate.side_effect = [mock_resp_bad, mock_resp_bad]

    result = await synthesis_service.synthesize(context, max_retries=1)

    assert len(result.candidates) == 0
    assert "error" in result.metadata

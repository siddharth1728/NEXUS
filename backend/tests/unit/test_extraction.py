"""Unit tests for the AI Extraction Service."""

import json
import uuid
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.core.ai.gateway import AIGateway
from app.core.ai.models import AIRequest, AIResponse
from app.models.document import DocumentChunk
from app.services.extraction_service import ExtractionService


@pytest.fixture
def chunk() -> DocumentChunk:
    return DocumentChunk(
        id=uuid.uuid4(),
        document_id=uuid.uuid4(),
        chunk_index=0,
        content="Registration closes at 5 PM on October 8. Submit the form.",
        structural_type="paragraph",
        source_location={"section": "Body", "block_index": 0},
    )


@pytest.fixture
def mock_gateway() -> Any:
    gw = MagicMock(spec=AIGateway)
    gw.generate = AsyncMock()
    return gw


@pytest.mark.asyncio
@pytest.mark.unit
async def test_extraction_service_success(
    mock_gateway: Any, in_memory_db_session: Any, chunk: DocumentChunk
) -> None:
    service = ExtractionService(ai_gateway=mock_gateway, session=in_memory_db_session)

    # We need to mock gateway.generate to return valid JSON list strings for each stage
    async def mock_generate(request: AIRequest) -> AIResponse:
        content = "[]"
        if request.system_instruction and "fact extractor" in request.system_instruction.lower():
            content = json.dumps(
                [
                    {
                        "statement": "Registration closes at 5 PM on October 8.",
                        "verbatim_quote": "Registration closes at 5 PM on October 8.",
                        "confidence": "HIGH",
                        "is_inferred": False,
                    }
                ]
            )
        elif (
            request.system_instruction
            and "named entity recognition" in request.system_instruction.lower()
        ):
            content = json.dumps(
                [{"name": "Registration", "type": "OTHER", "verbatim_quote": "Registration"}]
            )
        elif (
            request.system_instruction
            and "temporal extraction specialist" in request.system_instruction.lower()
        ):
            content = json.dumps(
                [
                    {
                        "temporal_expression": "October 8 at 5 PM",
                        "verbatim_quote": "5 PM on October 8",
                        "is_deadline": True,
                    }
                ]
            )
        elif (
            request.system_instruction
            and "requirements analyst" in request.system_instruction.lower()
        ):
            content = "[]"
        elif request.system_instruction and "task analyst" in request.system_instruction.lower():
            content = json.dumps(
                [{"action_statement": "Submit the form.", "verbatim_quote": "Submit the form."}]
            )

        return AIResponse(content=content, provider="mock", model="mock", is_structured=True)

    mock_gateway.generate.side_effect = mock_generate

    output = await service.extract_chunk(chunk)

    assert len(output.facts) == 1
    assert output.facts[0].statement == "Registration closes at 5 PM on October 8."
    assert output.facts[0].confidence == "HIGH"

    assert len(output.entities) == 1
    assert len(output.temporal_items) == 1
    assert len(output.requirements) == 0
    assert len(output.candidate_actions) == 1

    # Test persistence
    tenant_id = uuid.uuid4()
    persisted_facts = await service.persist_extracted_facts(
        tenant_id=tenant_id, document_id=chunk.document_id, chunk_id=chunk.id, output=output
    )

    assert len(persisted_facts) == 1
    assert persisted_facts[0].statement == "Registration closes at 5 PM on October 8."
    assert persisted_facts[0].tenant_id == tenant_id


@pytest.mark.asyncio
@pytest.mark.unit
async def test_extraction_service_repair_loop(
    mock_gateway: Any, in_memory_db_session: Any, chunk: DocumentChunk
) -> None:
    service = ExtractionService(ai_gateway=mock_gateway, session=in_memory_db_session)

    # First call returns malformed JSON, second call returns valid JSON
    responses = [
        AIResponse(
            content='[{"statement": "Broken JSON"',
            provider="mock",
            model="mock",
            is_structured=True,
        ),
        AIResponse(
            content='[{"statement": "Fixed fact", "verbatim_quote": "quote", "confidence": "HIGH", "is_inferred": false}]',
            provider="mock",
            model="mock",
            is_structured=True,
        ),
    ]

    async def mock_generate(request: AIRequest) -> AIResponse:
        # Just pop from predefined list
        if responses:
            return responses.pop(0)
        return AIResponse(content="[]", provider="mock", model="mock", is_structured=True)

    mock_gateway.generate.side_effect = mock_generate

    # We will test _execute_extraction_stage directly for this failure mode
    result = await service._execute_extraction_stage(
        "fact", "FACT_EXTRACTION_PROMPT.md", chunk.content, max_retries=1
    )

    assert len(result) == 1
    assert result[0]["statement"] == "Fixed fact"

    # Verify that it took two calls
    assert mock_gateway.generate.call_count == 2
    # Verify the second call prompt contained the repair instruction
    second_call_req = mock_gateway.generate.call_args_list[1][0][0]
    assert "Your previous output failed validation" in second_call_req.prompt


@pytest.mark.asyncio
@pytest.mark.unit
async def test_extraction_service_exhausted_retries(
    mock_gateway: Any, in_memory_db_session: Any, chunk: DocumentChunk
) -> None:
    service = ExtractionService(ai_gateway=mock_gateway, session=in_memory_db_session)

    # Returns malformed JSON endlessly
    async def mock_generate(request: AIRequest) -> AIResponse:
        return AIResponse(
            content='{"not_a_list": true}', provider="mock", model="mock", is_structured=True
        )

    mock_gateway.generate.side_effect = mock_generate

    result = await service._execute_extraction_stage(
        "fact", "FACT_EXTRACTION_PROMPT.md", chunk.content, max_retries=1
    )

    assert result == []
    assert mock_gateway.generate.call_count == 2

"""AI Extraction Service for NEXUS Phase 01F."""

import json
import uuid
from pathlib import Path
from typing import Any

from pydantic import ValidationError

from app.core.ai.gateway import AIGateway
from app.core.ai.models import AIRequest
from app.models.document import DocumentChunk
from app.models.fact import Fact
from app.schemas.extraction import (
    CandidateActionOutput,
    ChunkExtractionOutput,
    EntityOutput,
    FactOutput,
    RequirementOutput,
    TemporalOutput,
)


class ExtractionService:
    def __init__(self, ai_gateway: AIGateway, session: Any) -> None:
        self.ai = ai_gateway
        self.session = session
        self.prompts_dir = Path(__file__).parent.parent.parent.parent / "prompts" / "02-ai"

    def _load_prompt(self, filename: str) -> str:
        prompt_path = self.prompts_dir / filename
        return prompt_path.read_text(encoding="utf-8")

    async def _execute_extraction_stage(
        self, stage_name: str, prompt_file: str, chunk_content: str, max_retries: int = 1
    ) -> list[Any]:
        """
        Executes a specific extraction stage using the AI Gateway,
        validates the output, and performs controlled repair on failure.
        """
        system_instruction = self._load_prompt(prompt_file)

        # We ask for a JSON array as per the prompt rules
        prompt = f"Extract information from this chunk:\n\n{chunk_content}"

        request = AIRequest(
            provider="gemini",  # Default configured provider, could be parameterized
            model="gemini-3.1-pro",  # Example model
            prompt=prompt,
            system_instruction=system_instruction,
            temperature=0.0,
            require_structured_output=True,
        )

        for attempt in range(max_retries + 1):
            response = await self.ai.generate(request)

            try:
                # The prompt asks for a JSON list
                data = json.loads(response.content)
                if not isinstance(data, list):
                    raise ValueError("Expected a JSON list.")
                return data
            except (json.JSONDecodeError, ValueError) as e:
                if attempt == max_retries:
                    # If we exhaust retries, return empty or raise
                    # Returning empty list gracefully degrades missing info instead of halting whole pipeline
                    return []

                # Repair loop
                repair_prompt = (
                    f"Your previous output failed validation: {str(e)}.\n"
                    f"Please return ONLY a valid JSON list matching the schema.\n"
                    f"Do not invent facts. Original chunk:\n{chunk_content}"
                )
                request.prompt = repair_prompt

        return []

    async def extract_chunk(self, chunk: DocumentChunk) -> ChunkExtractionOutput:
        """Runs all extraction stages independently on a single chunk."""

        # 1. Fact Extraction
        raw_facts = await self._execute_extraction_stage(
            "fact", "FACT_EXTRACTION_PROMPT.md", chunk.content
        )
        facts = []
        for rf in raw_facts:
            try:
                facts.append(FactOutput(**rf))
            except ValidationError:
                pass  # Silently drop malformed items to prevent partial failure

        # 2. Entity Extraction
        raw_entities = await self._execute_extraction_stage(
            "entity", "ENTITY_EXTRACTION_PROMPT.md", chunk.content
        )
        entities = []
        for re in raw_entities:
            try:
                entities.append(EntityOutput(**re))
            except ValidationError:
                pass

        # 3. Temporal Extraction
        raw_temporal = await self._execute_extraction_stage(
            "temporal", "TEMPORAL_EXTRACTION_PROMPT.md", chunk.content
        )
        temporal_items = []
        for rt in raw_temporal:
            try:
                temporal_items.append(TemporalOutput(**rt))
            except ValidationError:
                pass

        # 4. Requirement Extraction
        raw_reqs = await self._execute_extraction_stage(
            "requirement", "REQUIREMENT_EXTRACTION_PROMPT.md", chunk.content
        )
        requirements = []
        for rr in raw_reqs:
            try:
                requirements.append(RequirementOutput(**rr))
            except ValidationError:
                pass

        # 5. Candidate Action Extraction
        raw_actions = await self._execute_extraction_stage(
            "candidate_action", "CANDIDATE_ACTION_EXTRACTION_PROMPT.md", chunk.content
        )
        actions = []
        for ra in raw_actions:
            try:
                actions.append(CandidateActionOutput(**ra))
            except ValidationError:
                pass

        return ChunkExtractionOutput(
            facts=facts,
            entities=entities,
            temporal_items=temporal_items,
            requirements=requirements,
            candidate_actions=actions,
        )

    async def persist_extracted_facts(
        self,
        tenant_id: uuid.UUID,
        document_id: uuid.UUID,
        chunk_id: uuid.UUID,
        output: ChunkExtractionOutput,
    ) -> list[Fact]:
        """Persists extracted facts to the DB as per canonical model requirements."""

        persisted_facts = []
        for fact_out in output.facts:
            # We bundle the non-persisted relations (entities, temp) into the chunk metadata
            # or we could store them inside the Fact if they are tightly coupled.
            # For Phase 01F, we strictly persist Fact models.

            fact = Fact(
                tenant_id=tenant_id,
                document_id=document_id,
                chunk_id=chunk_id,
                statement=fact_out.statement,
                verbatim_quote=fact_out.verbatim_quote,
                confidence=fact_out.confidence,
                metadata_={
                    "is_inferred": fact_out.is_inferred,
                    "extracted_by": "gemini-3.1-pro",
                },
            )
            self.session.add(fact)
            persisted_facts.append(fact)

        await self.session.flush()
        return persisted_facts

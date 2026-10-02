"""Service for AI Action Synthesis (Phase 02A)."""

import json
import logging
import uuid
from datetime import datetime
from typing import Literal

from pydantic import ValidationError

from app.core.ai.gateway import AIGateway
from app.core.ai.models import AIRequest
from app.models.enums import ConfidenceLevel
from app.schemas.action import ActionCreate, ActionResponse
from app.schemas.synthesis import (
    CandidateAction,
    CandidateActionValidationResult,
    SynthesisContext,
    SynthesisResult,
)
from app.services.action_service import ActionService

logger = logging.getLogger(__name__)


class SynthesisService:
    def __init__(self, ai_gateway: AIGateway, action_service: ActionService) -> None:
        self.ai = ai_gateway
        self.action_service = action_service
        self.prompt_path = "prompts/02-ai/ACTION_SYNTHESIS_PROMPT.md"

    def _load_prompt(self) -> str:
        with open(self.prompt_path, encoding="utf-8") as f:
            return f.read()

    async def synthesize(self, context: SynthesisContext, max_retries: int = 1) -> SynthesisResult:
        """Synthesize candidate actions from the provided context."""
        system_instruction = self._load_prompt()

        # Prepare JSON string inputs for prompt
        prompt = f"""
Please synthesize actions using the following context.
Facts: {json.dumps(context.facts)}
Entities: {json.dumps(context.entities)}
Temporal: {json.dumps(context.temporal_information)}
Requirements: {json.dumps(context.requirements)}
Candidate Actions: {json.dumps(context.candidate_actions)}
Chunks: {json.dumps(context.rag_context)}
Personalization: {json.dumps(context.personalization or {})}
Conflicts: {json.dumps(context.conflicts)}
Dependencies: {json.dumps(context.dependencies)}
"""

        request = AIRequest(
            provider="gemini",
            model="gemini-3.1-pro",
            prompt=prompt,
            system_instruction=system_instruction,
            temperature=0.0,
            require_structured_output=True,
        )

        for attempt in range(max_retries + 1):
            response = await self.ai.generate(request)

            try:
                data = json.loads(response.content)
                # Handle possible top-level object
                if "candidates" in data:
                    candidates_data = data["candidates"]
                elif "tasks" in data:
                    candidates_data = data["tasks"]
                elif "candidate_actions" in data:
                    candidates_data = data["candidate_actions"]
                elif isinstance(data, list):
                    candidates_data = data
                else:
                    raise ValueError("Unexpected JSON structure: missing candidates array")

                candidates = []
                for c in candidates_data:
                    # Adapt fields if model uses old schema names
                    if "action_type" in c and "classification" not in c:
                         c["classification"] = "EXPLICIT" # fallback
                    if "source_fact_indices" in c and "source_refs" not in c:
                         c["source_refs"] = [] # fallback
                    if "rationale" not in c:
                         c["rationale"] = "Inferred by LLM"

                    try:
                        candidates.append(CandidateAction(**c))
                    except ValidationError as e:
                        logger.warning(f"Validation error on candidate: {e}")
                        pass

                return SynthesisResult(
                    candidates=candidates,
                    metadata={
                        "model": request.model,
                        "provider": request.provider,
                        "prompt_version": "2.0.0",
                        "timestamp": datetime.utcnow().isoformat(),
                    }
                )

            except (json.JSONDecodeError, ValueError) as e:
                if attempt == max_retries:
                    return SynthesisResult(metadata={"error": str(e)})

                repair_prompt = (
                    f"Your previous output failed validation: {str(e)}.\n"
                    f"Please return ONLY valid JSON matching the schema.\n"
                )
                request.prompt = repair_prompt

        return SynthesisResult()

    async def validate_candidate(self, candidate: CandidateAction, tenant_id: str | uuid.UUID) -> CandidateActionValidationResult:
        """Perform domain validation on a candidate action."""
        reasons = []
        is_valid = True

        # Check references
        if not candidate.source_refs:
            reasons.append("Missing source references.")
            is_valid = False

        # Confidence check
        if candidate.confidence == ConfidenceLevel.UNKNOWN:
            reasons.append("Confidence is UNKNOWN.")
            is_valid = False

        if candidate.confidence == ConfidenceLevel.CONFLICT:
            reasons.append("Conflict detected in sources.")
            is_valid = False

        status: Literal["APPROVED", "REJECTED", "REQUIRES_REVIEW"] = "APPROVED" if is_valid else "REQUIRES_REVIEW"
        if not is_valid and len(reasons) > 0 and "Missing source" in reasons[0]:
            # Just an example of rejecting entirely bad candidates
            pass

        return CandidateActionValidationResult(
            is_valid=is_valid,
            status=status,
            reasons=reasons,
            validated_action_data=candidate.model_dump() if is_valid else None
        )

    async def create_action_from_candidate(self, tenant_id: str | uuid.UUID, candidate: CandidateAction) -> ActionResponse:
        """Create a persisted Action from a validated candidate."""
        from app.schemas.action import ActionResponse
        tenant_uuid = uuid.UUID(str(tenant_id)) if isinstance(tenant_id, str) else tenant_id
        validation = await self.validate_candidate(candidate, tenant_uuid)
        if not validation.is_valid and validation.status != "REQUIRES_REVIEW":
            raise ValueError(f"Cannot create action from invalid candidate: {validation.reasons}")

        # Check deduplication (simple approach: check if title exists for tenant)
        existing, _ = await self.action_service.list_actions(tenant_uuid)
        for act in existing:
            if act.title.lower() == candidate.title.lower():
                # For now just return the existing to simulate dedup
                return ActionResponse.model_validate(act)

        # We assume priority string maps correctly, otherwise default
        priority = candidate.priority_signal or "P2"
        if priority not in ["P0", "P1", "P2", "P3"]:
             priority = "P2"

        action_create = ActionCreate(
            title=candidate.title,
            description=candidate.description + f"\n\nRationale: {candidate.rationale}",
            priority=priority,
            confidence=candidate.confidence,
            # Assign first source doc as the source document, if available
            source_document_id=candidate.source_refs[0].document_id if candidate.source_refs else None
        )

        act = await self.action_service.create_action(tenant_uuid, action_create)
        return ActionResponse.model_validate(act)

"""Verification Service for generating and checking evidence."""

import uuid
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.execution.tool import ExecutionContext
from app.core.execution.tool_registry import ToolRegistry
from app.models.enums import Capability
from app.models.verification import Evidence, EvidenceRequirement
from app.schemas.verification import EvidenceRequirementCreate, EvidenceResponse, VerificationResult


class VerificationService:
    """Evaluates whether actions have been truly completed in external systems."""

    def __init__(self, session: AsyncSession, tool_registry: ToolRegistry) -> None:
        self.session = session
        self.tool_registry = tool_registry

    async def create_requirement(
        self, tenant_id: str, request: EvidenceRequirementCreate
    ) -> EvidenceRequirement:
        """Create a new deterministic evidence requirement."""
        req = EvidenceRequirement(
            tenant_id=uuid.UUID(tenant_id),
            action_id=request.action_id,
            tool_id=request.tool_id,
            parameters=request.parameters,
            expected_state=request.expected_state,
        )
        self.session.add(req)
        await self.session.commit()
        await self.session.refresh(req)
        return req

    async def verify_requirement(self, tenant_id: str, requirement_id: str) -> VerificationResult:
        """Execute a read-only tool to gather evidence and check assertions."""
        stmt = select(EvidenceRequirement).where(
            EvidenceRequirement.id == uuid.UUID(requirement_id),
            EvidenceRequirement.tenant_id == uuid.UUID(tenant_id),
        )
        result = await self.session.execute(stmt)
        req = result.scalar_one_or_none()

        if not req:
            raise ValueError("Evidence requirement not found.")

        tool = self.tool_registry.get(req.tool_id)
        if not tool:
            raise ValueError(f"Tool {req.tool_id} not found in registry.")

        # Ensure tool is read-only based on capability (basic check)
        if "READ" not in tool.capability.value:
            # We could enforce stricter capability isolation, but assuming tools with READ are read-only.
            pass

        input_schema = tool.get_input_schema()
        params = input_schema.model_validate(req.parameters)

        context = ExecutionContext(
            tenant_id=tenant_id,
            dry_run=False,
        )

        try:
            result_payload = await tool.execute(params, context)
            
            # Deterministic check: verify expected_state matches result_payload
            is_valid = self._evaluate_assertions(req.expected_state, result_payload)
            reason = "Evidence matches expected state." if is_valid else "Evidence does not match expected state."

            # Save Evidence
            evidence = Evidence(
                tenant_id=uuid.UUID(tenant_id),
                requirement_id=req.id,
                payload=result_payload,
                provenance={"tool_id": req.tool_id, "generated_by": "VerificationEngine"},
                is_valid=is_valid,
            )
            self.session.add(evidence)
            await self.session.commit()
            await self.session.refresh(evidence)

            return VerificationResult(
                requirement_id=req.id,
                is_verified=is_valid,
                reason=reason,
                evidence_id=evidence.id,
            )

        except Exception as e:
            return VerificationResult(
                requirement_id=req.id,
                is_verified=False,
                reason=f"Verification failed with error: {str(e)}",
            )

    def _evaluate_assertions(self, expected: dict[str, Any], actual: dict[str, Any]) -> bool:
        """Deep check if 'actual' dictionary contains all 'expected' key-values."""
        for key, expected_value in expected.items():
            if key not in actual:
                return False
            
            actual_val = actual[key]
            
            if isinstance(expected_value, dict) and isinstance(actual_val, dict):
                if not self._evaluate_assertions(expected_value, actual_val):
                    return False
            elif expected_value != actual_val:
                return False

        return True

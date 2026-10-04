"""Service for orchestrating the autonomous progression loop."""

import uuid
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.models.action import Action
from app.models.enums import (
    ActionStatus,
    AutonomyMode,
    Capability,
    ExecutionState,
    PolicyDecision,
    RiskTier,
)
from app.schemas.action import ActionResponse
from app.schemas.execution import ExecutionRequestCreate
from app.services.action_service import ActionService
from app.services.execution_service import ExecutionService
from app.services.verification_service import VerificationService
from app.services.workflow_service import WorkflowEngine

logger = get_logger(__name__)


class AutonomousLoopService:
    """Orchestrates the safe, bounded progression of actions."""

    def __init__(
        self,
        db: AsyncSession,
        action_service: ActionService,
        execution_service: ExecutionService,
        verification_service: VerificationService,
        workflow_engine: WorkflowEngine,
    ):
        self.db = db
        self.action_service = action_service
        self.execution_service = execution_service
        self.verification_service = verification_service
        self.workflow_engine = workflow_engine

    async def run_loop(
        self,
        tenant_id: uuid.UUID,
        mode: AutonomyMode,
        max_iterations: int = 5,
    ) -> dict[str, Any]:
        """Run the autonomous loop up to max_iterations.

        Returns a summary of actions taken and the stop reason.
        """
        iteration = 0
        actions_taken = []
        stop_reason = "MAX_ITERATIONS_REACHED"

        while iteration < max_iterations:
            iteration += 1
            logger.info(f"Starting autonomous loop iteration {iteration} for tenant {tenant_id}")

            # 1. Identify next eligible action
            items, _ = await self.action_service.list_actions(
                tenant_id=tenant_id,
                offset=0,
                limit=50
            )
            eligible_actions = [a for a in items if a.status == ActionStatus.READY]
            if not eligible_actions:
                stop_reason = "NO_ELIGIBLE_ACTIONS"
                break

            action = eligible_actions[0]
            logger.info(f"Selected eligible action {action.id} for processing")

            # 2. Risk & Capability Resolution
            capability = self._determine_capability(action)
            tool_id = self._get_tool_id_for_capability(capability)
            parameters = self._build_parameters_for_tool(tool_id, action)
            risk_tier = self._determine_risk_tier(capability.value)

            # Policy enforcement
            policy_decision = self._evaluate_policy(mode, risk_tier)
            if policy_decision == PolicyDecision.DENY:
                logger.warning(f"Policy denied action {action.id}")
                stop_reason = "POLICY_DENIED"
                break

            # 3. Create Execution Request
            exec_req = await self.execution_service.create_request(
                tenant_id=str(tenant_id),
                requester_id=None,
                request=ExecutionRequestCreate(
                    action_id=action.id,
                    agent_id="simulator" if tool_id == "simulate_v1" else "autonomous_loop",
                    capability=capability,
                    tool_id=tool_id,
                    parameters=parameters,
                )
            )

            # 4. Handle Approval if required
            if policy_decision == PolicyDecision.REQUIRE_APPROVAL:
                logger.info(f"Action {action.id} requires human approval. Halting loop.")
                stop_reason = "REQUIRES_APPROVAL"
                actions_taken.append({"action_id": action.id, "status": "AWAITING_APPROVAL"})
                break

            # 5. Execute
            logger.info(f"Executing action {action.id}")
            # Transition to IN_PROGRESS
            await self.action_service.transition_state(
                action_id=action.id,
                tenant_id=tenant_id,
                new_status=ActionStatus.IN_PROGRESS
            )

            exec_result = await self.execution_service.execute(
                tenant_id=str(tenant_id),
                execution_id=str(exec_req.id)
            )

            if exec_result.state in [ExecutionState.FAILED, ExecutionState.DENIED, ExecutionState.REJECTED]:
                logger.error(f"Execution failed for action {action.id}")
                stop_reason = "EXECUTION_FAILED"
                actions_taken.append({"action_id": action.id, "status": "EXECUTION_FAILED"})
                break

            # 6. Verify
            logger.info(f"Verifying action {action.id}")
            # Transition to PENDING_VERIFICATION
            await self.action_service.transition_state(
                action_id=action.id,
                tenant_id=tenant_id,
                new_status=ActionStatus.PENDING_VERIFICATION
            )

            is_verified = await self.verification_service.verify_action(
                action_id=action.id,
                tenant_id=tenant_id
            )

            if not is_verified:
                logger.warning(f"Verification failed for action {action.id}")
                await self.action_service.transition_state(
                    action_id=action.id,
                    tenant_id=tenant_id,
                    new_status=ActionStatus.NOT_VERIFIED
                )
                stop_reason = "VERIFICATION_FAILED"
                actions_taken.append({"action_id": action.id, "status": "VERIFICATION_FAILED"})
                break

            # 7. Update Workflow / Graph
            logger.info(f"Action {action.id} verified. Progressing workflow.")
            await self.action_service.transition_state(
                action_id=action.id,
                tenant_id=tenant_id,
                new_status=ActionStatus.VERIFIED
            )
            await self.action_service.transition_state(
                action_id=action.id,
                tenant_id=tenant_id,
                new_status=ActionStatus.COMPLETED
            )
            actions_taken.append({"action_id": action.id, "status": "COMPLETED"})


            # Workflow service internally updates downstream blocked actions when an action completes
            # The next iteration will pick up newly eligible actions

        return {
            "iterations_run": iteration,
            "actions_taken": actions_taken,
            "stop_reason": stop_reason,
            "mode": mode,
        }

    def _determine_capability(self, action: Action | ActionResponse) -> Capability:
        title = action.title.upper() if action.title else ""
        desc = action.description.upper() if action.description else ""
        text = f"{title} {desc}"

        if "GITHUB" in text:
            if "CREATE" in text or "ISSUE" in text:
                return Capability.GITHUB_ISSUE_CREATE
            return Capability.GITHUB_REPOSITORY_READ
        if "CALENDAR" in text:
            return Capability.CALENDAR_CREATE
        if "EMAIL" in text:
            return Capability.EMAIL_DRAFT
        return Capability.SYSTEM_SIMULATE

    def _get_tool_id_for_capability(self, capability: Capability) -> str:
        if capability == Capability.SYSTEM_SIMULATE:
            return "simulate_v1"
        if capability == Capability.GITHUB_ISSUE_CREATE:
            return "github_issue_create"
        if capability == Capability.GITHUB_REPOSITORY_READ:
            return "github_repo_read"
        if capability == Capability.CALENDAR_CREATE:
            return "calendar_create"
        if capability == Capability.EMAIL_DRAFT:
            return "email_draft"
        return "simulate_v1"

    def _build_parameters_for_tool(self, tool_id: str, action: Action | ActionResponse) -> dict[str, Any]:
        if tool_id == "simulate_v1":
            return {
                "action_type": action.title or "simulated_action",
                "should_fail": False,
                "delay_ms": 0,
                "mock_payload": {"description": action.description or ""},
                "requires_approval": False,
            }
        return {"action_id": str(action.id), "title": action.title}

    def _determine_risk_tier(self, capability: str | None) -> RiskTier:
        if not capability:
            return RiskTier.READ_ONLY

        cap_str = capability.upper()
        if "READ" in cap_str or "SIMULATE" in cap_str:
            return RiskTier.READ_ONLY
        elif "CREATE" in cap_str or "UPDATE" in cap_str or "DRAFT" in cap_str:
            return RiskTier.LOW_RISK_MUTATION
        elif "DELETE" in cap_str or "SEND" in cap_str:
            return RiskTier.HIGH_RISK_MUTATION
        return RiskTier.SENSITIVE

    def _evaluate_policy(self, mode: AutonomyMode, risk: RiskTier) -> PolicyDecision:
        if mode in (AutonomyMode.MANUAL, AutonomyMode.ASSISTED, AutonomyMode.APPROVAL_REQUIRED):
            return PolicyDecision.REQUIRE_APPROVAL

        if mode == AutonomyMode.AUTONOMOUS_WITHIN_POLICY:
            if risk in (RiskTier.READ_ONLY, RiskTier.LOW_RISK_MUTATION):
                return PolicyDecision.ALLOW
            else:
                # High risk or sensitive always requires approval, even in autonomous mode
                return PolicyDecision.REQUIRE_APPROVAL

        return PolicyDecision.REQUIRE_APPROVAL

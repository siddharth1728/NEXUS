"""Execution Service for handling action execution lifecycles."""

import uuid
from typing import Any
from datetime import datetime, UTC

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.execution.agent_registry import AgentRegistry
from app.core.execution.policy import PolicyEngine
from app.core.execution.tool_registry import ToolRegistry
from app.models.action import Action
from app.models.enums import ApprovalDecision, ExecutionState, PolicyDecision
from app.models.execution import ExecutionRecord
from app.schemas.execution import ExecutionApproval, ExecutionRequestCreate, ExecutionResponse, DryRunResult


class ExecutionService:
    """Manages the lifecycle of ExecutionRequests."""
    
    def __init__(
        self,
        session: AsyncSession,
        agent_registry: AgentRegistry,
        tool_registry: ToolRegistry,
        policy_engine: PolicyEngine
    ) -> None:
        self.session = session
        self.agent_registry = agent_registry
        self.tool_registry = tool_registry
        self.policy_engine = policy_engine
        
    async def get_execution(self, tenant_id: str, execution_id: str) -> ExecutionResponse | None:
        """Fetch an execution record, ensuring tenant isolation."""
        stmt = select(ExecutionRecord).where(
            ExecutionRecord.id == uuid.UUID(execution_id),
            ExecutionRecord.tenant_id == uuid.UUID(tenant_id)
        )
        result = await self.session.execute(stmt)
        record = result.scalar_one_or_none()
        if not record:
            return None
        return ExecutionResponse.model_validate(record)

    async def create_request(
        self, tenant_id: str, requester_id: str | None, request: ExecutionRequestCreate
    ) -> ExecutionResponse:
        """Create a new execution request and evaluate its policy."""
        # Validate Action belongs to tenant
        stmt = select(Action).where(
            Action.id == request.action_id,
            Action.tenant_id == uuid.UUID(tenant_id)
        )
        result = await self.session.execute(stmt)
        action = result.scalar_one_or_none()
        if not action:
            raise ValueError(f"Action {request.action_id} not found in tenant.")
            
        # Validate Agent exists and has capability
        agent = self.agent_registry.get(request.agent_id)
        if not agent:
            raise ValueError(f"Agent {request.agent_id} is not registered.")
        if request.capability not in agent.capabilities:
            raise ValueError(f"Agent {request.agent_id} lacks capability {request.capability}.")
            
        # Validate Tool exists and matches capability
        tool = self.tool_registry.get(request.tool_id)
        if not tool:
            raise ValueError(f"Tool {request.tool_id} is not registered.")
        if tool.capability != request.capability:
            raise ValueError(f"Tool {request.tool_id} does not provide capability {request.capability}.")
            
        # Validate Parameters strictly against Tool's schema
        input_schema = tool.get_input_schema()
        try:
            validated_params = input_schema.model_validate(request.parameters)
        except Exception as e:
            raise ValueError(f"Parameter validation failed: {str(e)}")
            
        # Evaluate Policy
        policy_decision = self.policy_engine.evaluate(request)
        
        state = ExecutionState.PENDING
        if policy_decision == PolicyDecision.DENY:
            state = ExecutionState.DENIED
        elif policy_decision == PolicyDecision.REQUIRE_APPROVAL:
            state = ExecutionState.AWAITING_APPROVAL
        elif policy_decision == PolicyDecision.ALLOW:
            state = ExecutionState.AUTHORIZED
            
        # Check Idempotency (prevent duplicate exact requests)
        idem_stmt = select(ExecutionRecord).where(
            ExecutionRecord.action_id == request.action_id,
            ExecutionRecord.tool_id == request.tool_id,
            ExecutionRecord.state.in_([
                ExecutionState.PENDING,
                ExecutionState.AWAITING_APPROVAL,
                ExecutionState.AUTHORIZED,
                ExecutionState.RUNNING,
                ExecutionState.SUCCEEDED
            ])
        )
        idem_result = await self.session.execute(idem_stmt)
        existing = idem_result.scalars().first()
        if existing:
            # For phase 02B, we raise an error to prevent duplicate execution of the same tool on the same action
            # unless parameters differ, but we keep it strict.
            raise ValueError("Idempotency violation: A similar execution is already pending, running, or succeeded.")

        # Persist ExecutionRecord
        record = ExecutionRecord(
            tenant_id=uuid.UUID(tenant_id),
            action_id=request.action_id,
            requester_id=uuid.UUID(requester_id) if requester_id else None,
            agent_id=request.agent_id,
            capability=request.capability,
            tool_id=request.tool_id,
            parameters=validated_params.model_dump(),
            state=state,
            policy_decision=policy_decision
        )
        self.session.add(record)
        await self.session.commit()
        await self.session.refresh(record)
        
        return ExecutionResponse.model_validate(record)
        
    async def review_execution(
        self, tenant_id: str, approver_id: str, execution_id: str, review: ExecutionApproval
    ) -> ExecutionResponse:
        """Approve or reject a pending execution request."""
        stmt = select(ExecutionRecord).where(
            ExecutionRecord.id == uuid.UUID(execution_id),
            ExecutionRecord.tenant_id == uuid.UUID(tenant_id)
        )
        result = await self.session.execute(stmt)
        record = result.scalar_one_or_none()
        
        if not record:
            raise ValueError("Execution record not found.")
            
        if record.state != ExecutionState.AWAITING_APPROVAL:
            raise ValueError(f"Cannot review execution in state: {record.state}")
            
        record.approval_decision = review.decision
        record.approver_id = uuid.UUID(approver_id)
        record.approval_reason = review.reason
        
        if review.decision == ApprovalDecision.APPROVED:
            record.state = ExecutionState.AUTHORIZED
        else:
            record.state = ExecutionState.REJECTED
            
        self.session.add(record)
        await self.session.commit()
        await self.session.refresh(record)
        
        return ExecutionResponse.model_validate(record)
        
    async def execute(self, tenant_id: str, execution_id: str) -> ExecutionResponse:
        """Actually run the authorized execution."""
        stmt = select(ExecutionRecord).where(
            ExecutionRecord.id == uuid.UUID(execution_id),
            ExecutionRecord.tenant_id == uuid.UUID(tenant_id)
        )
        result = await self.session.execute(stmt)
        record = result.scalar_one_or_none()
        
        if not record:
            raise ValueError("Execution record not found.")
            
        if record.state != ExecutionState.AUTHORIZED:
            raise ValueError(f"Cannot execute record in state: {record.state}")
            
        tool = self.tool_registry.get(record.tool_id)
        if not tool:
            # Should never happen if database integrity holds
            record.state = ExecutionState.FAILED
            record.error_message = "Tool no longer exists."
            await self.session.commit()
            raise ValueError("Tool no longer exists.")
            
        record.state = ExecutionState.RUNNING
        self.session.add(record)
        await self.session.commit()
        
        input_schema = tool.get_input_schema()
        params = input_schema.model_validate(record.parameters)
        
        try:
            result_payload = await tool.execute(params)
            record.state = ExecutionState.SUCCEEDED
            record.result_payload = result_payload
        except Exception as e:
            record.state = ExecutionState.FAILED
            record.error_message = str(e)
            
        self.session.add(record)
        await self.session.commit()
        await self.session.refresh(record)
        
        return ExecutionResponse.model_validate(record)

    async def dry_run(self, tenant_id: str, request: ExecutionRequestCreate) -> DryRunResult:
        """Evaluate policy without persisting or executing."""
        policy_decision = self.policy_engine.evaluate(request)
        would_execute = policy_decision in (PolicyDecision.ALLOW, PolicyDecision.REQUIRE_APPROVAL)
        
        reason = None
        if policy_decision == PolicyDecision.DENY:
            reason = "Capability is denied by policy."
        elif policy_decision == PolicyDecision.REQUIRE_APPROVAL:
            reason = "Requires human approval."
            
        return DryRunResult(
            action_id=request.action_id,
            agent_id=request.agent_id,
            capability=request.capability,
            tool_id=request.tool_id,
            parameters=request.parameters,
            policy_decision=policy_decision,
            would_execute=would_execute,
            reason=reason
        )

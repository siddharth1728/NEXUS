"""Workflow Engine Service."""

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enums import ActionStatus
from app.services.action_service import ActionService


class WorkflowEngine:
    """Manages the progression of Action workflows and dependencies."""

    def __init__(self, session: AsyncSession, action_service: ActionService) -> None:
        self.session = session
        self.action_service = action_service

    async def evaluate_dependencies(self, tenant_id: str, action_id: str) -> None:
        """Evaluate if an action should be unblocked based on its dependencies."""
        action_uuid = uuid.UUID(action_id)
        tenant_uuid = uuid.UUID(tenant_id)
        
        # Get edges where this action is the source (it depends on target)
        dependencies, _ = await self.action_service.get_dependencies(action_uuid, tenant_uuid, limit=100)
        
        all_resolved = True
        for edge in dependencies:
            target = await self.action_service.get_action(edge.target_id, tenant_uuid)
            # Only VERIFIED or COMPLETED states resolve a dependency
            if target.status not in (ActionStatus.VERIFIED, ActionStatus.COMPLETED):
                all_resolved = False
                break
        
        # Unblock if currently blocked and dependencies resolved
        action = await self.action_service.get_action(action_uuid, tenant_uuid)
        if all_resolved and action.status == ActionStatus.BLOCKED:
            await self.action_service.transition_state(action_uuid, tenant_uuid, ActionStatus.READY)
        elif not all_resolved and action.status == ActionStatus.READY:
            await self.action_service.transition_state(action_uuid, tenant_uuid, ActionStatus.BLOCKED)

    async def process_verification_result(self, tenant_id: str, action_id: str, is_verified: bool, reason: str) -> None:
        """Process a verification result and update action status accordingly."""
        action_uuid = uuid.UUID(action_id)
        tenant_uuid = uuid.UUID(tenant_id)
        
        action = await self.action_service.get_action(action_uuid, tenant_uuid)
        
        if is_verified:
            # If verification passes, we go to VERIFIED
            await self.action_service.transition_state(action_uuid, tenant_uuid, ActionStatus.VERIFIED)
            
            # Since this action is VERIFIED, we must evaluate actions that depend on it
            dependents, _ = await self.action_service.get_dependents(action_uuid, tenant_uuid, limit=100)
            for edge in dependents:
                await self.evaluate_dependencies(tenant_id, str(edge.source_id))
        else:
            # If verification fails, it could be NOT_VERIFIED or REQUIRES_REVIEW.
            # We'll use REQUIRES_REVIEW as the default for human intervention if it's not a hard failure.
            await self.action_service.transition_state(action_uuid, tenant_uuid, ActionStatus.REQUIRES_REVIEW)

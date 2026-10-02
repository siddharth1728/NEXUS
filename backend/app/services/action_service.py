"""Action Management Service."""

import uuid

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import ConflictError, GraphCycleError, NotFoundError
from app.domain.action_graph import check_for_cycles
from app.models.action import Action, ActionEdge
from app.models.enums import ActionStatus, EdgeRelationType
from app.repositories.action import ActionEdgeRepository, ActionRepository
from app.schemas.action import ActionCreate, ActionUpdate

# Valid state transitions derived from Action Graph Conceptual Model
VALID_ACTION_TRANSITIONS = {
    ActionStatus.CANDIDATE: {ActionStatus.REJECTED, ActionStatus.READY, ActionStatus.BLOCKED},
    ActionStatus.BLOCKED: {ActionStatus.READY},
    ActionStatus.READY: {ActionStatus.IN_PROGRESS, ActionStatus.CANCELLED},
    ActionStatus.IN_PROGRESS: {
        ActionStatus.BLOCKED,
        ActionStatus.PENDING_VERIFICATION,
        ActionStatus.FAILED,
    },
    ActionStatus.PENDING_VERIFICATION: {ActionStatus.COMPLETED, ActionStatus.IN_PROGRESS},
}


class ActionService:
    """Application use-case service for Action management."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.action_repo = ActionRepository(session)
        self.edge_repo = ActionEdgeRepository(session)

    async def create_action(self, tenant_id: uuid.UUID, data: ActionCreate) -> Action:
        """Create a new action for a tenant."""
        action = Action(
            tenant_id=tenant_id,
            title=data.title,
            description=data.description,
            priority=data.priority,
            due_date=data.due_date,
            is_hard_deadline=data.is_hard_deadline,
            assignee_id=data.assignee_id,
            confidence=data.confidence,
            source_document_id=data.source_document_id,
            status=ActionStatus.CANDIDATE,  # Default state
        )
        return await self.action_repo.create(action)

    async def get_action(self, action_id: uuid.UUID, tenant_id: uuid.UUID) -> Action:
        """Get an action with strict tenant isolation."""
        action = await self.action_repo.get_action_for_tenant(action_id, tenant_id)
        if not action:
            raise NotFoundError("Action", str(action_id))
        return action

    async def list_actions(
        self, tenant_id: uuid.UUID, offset: int = 0, limit: int = 50
    ) -> list[Action]:
        """List actions for a tenant."""
        return await self.action_repo.list_for_tenant(tenant_id, offset, limit)

    async def update_action(
        self, action_id: uuid.UUID, tenant_id: uuid.UUID, data: ActionUpdate
    ) -> Action:
        """Update action metadata."""
        action = await self.get_action(action_id, tenant_id)

        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(action, key, value)

        await self.session.flush()
        return action

    async def transition_state(
        self, action_id: uuid.UUID, tenant_id: uuid.UUID, new_status: ActionStatus
    ) -> Action:
        """Transition action state, enforcing valid state machine rules."""
        action = await self.get_action(action_id, tenant_id)

        if action.status == new_status:
            return action  # No-op

        valid_next_states = VALID_ACTION_TRANSITIONS.get(action.status, set())
        if new_status not in valid_next_states:
            raise ConflictError(f"Invalid transition from {action.status} to {new_status}")

        action.status = new_status
        await self.session.flush()
        return action

    async def create_dependency(
        self,
        tenant_id: uuid.UUID,
        source_id: uuid.UUID,
        target_id: uuid.UUID,
        relation_type: EdgeRelationType,
        metadata: dict | None = None,
    ) -> ActionEdge:
        """Create a dependency edge between two actions, enforcing tenant isolation and cycle detection."""
        # 1. Ensure both actions exist and belong to the tenant
        source = await self.get_action(source_id, tenant_id)
        target = await self.get_action(target_id, tenant_id)

        # 3. Reject self-reference
        if source.id == target.id:
            raise GraphCycleError(
                cycle_path=[str(source.id)], message="Self-referencing edges are not allowed."
            )

        # 4. Check if edge already exists
        existing = await self.edge_repo.get_edge(source.id, target.id, relation_type)
        if existing:
            raise ConflictError("Dependency edge already exists.")

        # Prepare new edge
        new_edge = ActionEdge(
            tenant_id=tenant_id,
            source_id=source.id,
            target_id=target.id,
            relation_type=relation_type,
            metadata_payload=metadata or {},
        )

        # 5. Cycle detection
        # For simplicity and correctness in this phase, we fetch all edges in the tenant graph to detect cycles.
        # A more optimal approach in production would use recursive CTEs or limit fetch to reachable nodes.
        all_edges = await self.edge_repo.list(limit=10000, filters={"tenant_id": tenant_id})
        check_for_cycles(new_edge, all_edges)

        # 6. Persist
        try:
            edge = await self.edge_repo.create(new_edge)
            return edge
        except IntegrityError as e:
            await self.session.rollback()
            raise ConflictError("Dependency edge already exists or constraint failed.") from e

    async def get_dependencies(
        self, action_id: uuid.UUID, tenant_id: uuid.UUID
    ) -> list[ActionEdge]:
        """Get edges where this action is the source (i.e. depends on target)."""
        await self.get_action(action_id, tenant_id)  # Validate existence & tenant
        return await self.edge_repo.get_dependencies_for_action(
            action_id, EdgeRelationType.DEPENDS_ON
        )

    async def get_dependents(self, action_id: uuid.UUID, tenant_id: uuid.UUID) -> list[ActionEdge]:
        """Get edges where this action is the target (i.e. sources that depend on this action)."""
        await self.get_action(action_id, tenant_id)  # Validate existence & tenant
        return await self.edge_repo.get_dependents_for_action(
            action_id, EdgeRelationType.DEPENDS_ON
        )

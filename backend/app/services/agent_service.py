"""Agent Delegation Service."""

import uuid
from typing import Any

from app.core.execution.agent_registry import AgentRegistry
from app.core.execution.policy import PolicyEngine
from app.core.execution.tool_registry import ToolRegistry
from app.core.logging import get_logger
from app.models.enums import PolicyDecision
from app.schemas.agent import Agent

logger = get_logger(__name__)


class AgentService:
    """Handles agent delegation and constrained execution."""

    def __init__(
        self,
        agent_registry: AgentRegistry,
        tool_registry: ToolRegistry,
        policy_engine: PolicyEngine,
    ):
        self.agent_registry = agent_registry
        self.tool_registry = tool_registry
        self.policy_engine = policy_engine

    def delegate_task(self, tenant_id: uuid.UUID, agent_id: str, task: str) -> dict[str, Any]:
        """Delegate a task to a specific agent if permitted."""
        agent = self.agent_registry.get(agent_id)
        if not agent:
            raise ValueError(f"Agent {agent_id} not found in registry")

        # 1. Scope Verification
        logger.info(f"Delegating task to agent {agent.name} for tenant {tenant_id}")

        # 2. Agent tries to resolve intent to a tool
        # In a real system, the agent uses LLM to map task -> tool. We mock this:
        requested_tool = self._mock_llm_tool_selection(agent, task)

        if not requested_tool:
            return {"status": "FAILED", "reason": "No suitable tool found by agent"}

        # 3. Verify Agent Capability Bounds
        if requested_tool.capability not in agent.capabilities:
            logger.warning(f"Agent {agent.id} attempted to use ungranted capability {requested_tool.capability}")
            return {"status": "BLOCKED", "reason": "UNAUTHORIZED_CAPABILITY"}

        # 4. Global Policy Enforcement
        from app.schemas.execution import ExecutionRequestCreate
        exec_req = ExecutionRequestCreate(
            action_id=uuid.uuid4(),
            agent_id=agent.id,
            capability=requested_tool.capability,
            tool_id=requested_tool.tool_id,
            parameters={},
        )
        decision = self.policy_engine.evaluate(exec_req)

        if decision == PolicyDecision.DENY:
            return {"status": "BLOCKED", "reason": "POLICY_DENIED"}
        elif decision == PolicyDecision.REQUIRE_APPROVAL:
            return {"status": "REQUIRES_REVIEW", "reason": "APPROVAL_REQUIRED", "tool": requested_tool.tool_id}

        # 5. Execute if allowed
        return {"status": "SUCCESS", "tool_executed": requested_tool.tool_id, "result": "Delegated task completed."}

    def _mock_llm_tool_selection(self, agent: Agent, task: str) -> Any:
        # Mocking the agent selecting a tool based on its bounded capabilities
        for cap in agent.capabilities:
            tools = self.tool_registry.resolve_by_capability(cap)
            if tools:
                return tools[0]
        return None


"""Agent Registry for NEXUS Agents."""

from app.schemas.agent import Agent


class AgentRegistry:
    """Lightweight in-memory registry for system agents."""

    def __init__(self) -> None:
        self._agents: dict[str, Agent] = {}

    def register(self, agent: Agent) -> None:
        """Register an agent by its ID."""
        self._agents[agent.id] = agent

    def get(self, agent_id: str) -> Agent | None:
        """Retrieve an agent by its ID."""
        return self._agents.get(agent_id)

    def list_all(self) -> list[Agent]:
        """List all registered agents."""
        return list(self._agents.values())

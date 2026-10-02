"""Agent Router."""


from app.core.execution.tool_registry import ToolRegistry
from app.models.enums import Capability
from app.schemas.tool import ToolResolutionResult


class AgentRouter:
    """Routes an execution intent to the appropriate registered tool."""

    def __init__(self, tool_registry: ToolRegistry) -> None:
        self.tool_registry = tool_registry

    def resolve_intent(self, intent: str) -> ToolResolutionResult | None:
        """Map an abstract intent to a specific tool via capability."""
        # A real system would use semantic matching. Here we map explicitly for Phase 02B.
        intent_lower = intent.lower()

        target_capability = None
        if "github" in intent_lower and "issue" in intent_lower:
            target_capability = Capability.GITHUB_ISSUE_CREATE
        elif "email" in intent_lower:
            target_capability = Capability.EMAIL_SEND
        elif "calendar" in intent_lower and "create" in intent_lower:
            target_capability = Capability.CALENDAR_CREATE
        elif "simulate" in intent_lower:
            target_capability = Capability.SYSTEM_SIMULATE

        if not target_capability:
            return None

        candidates = self.tool_registry.resolve_by_capability(target_capability)
        if not candidates:
            return None

        # Return the first registered tool for the capability
        return ToolResolutionResult(
            capability=target_capability,
            tool_id=candidates[0].tool_id
        )

"""Tool Registry for NEXUS Tools."""


from app.core.execution.tool import BaseTool
from app.models.enums import Capability


class ToolRegistry:
    """Lightweight in-memory registry for execution tools."""

    def __init__(self) -> None:
        self._tools: dict[str, BaseTool] = {}

    def register(self, tool: BaseTool) -> None:
        """Register a tool by its ID."""
        self._tools[tool.tool_id] = tool

    def get(self, tool_id: str) -> BaseTool | None:
        """Retrieve a tool by its ID."""
        return self._tools.get(tool_id)

    def resolve_by_capability(self, capability: Capability) -> list[BaseTool]:
        """Find tools that provide the given capability."""
        return [tool for tool in self._tools.values() if tool.capability == capability]

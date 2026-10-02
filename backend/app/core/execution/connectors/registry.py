
from app.core.execution.connectors.base import BaseConnector


class ConnectorRegistry:
    """Registry for external system connectors."""

    def __init__(self) -> None:
        self._connectors: dict[str, BaseConnector] = {}

    def register(self, connector: BaseConnector) -> None:
        """Register a connector instance."""
        self._connectors[connector.provider] = connector

    def get(self, provider: str) -> BaseConnector | None:
        """Get a connector by provider name."""
        return self._connectors.get(provider)

    def list_all(self) -> list[BaseConnector]:
        """List all registered connectors."""
        return list(self._connectors.values())

    def clear(self) -> None:
        """Clear all registered connectors (primarily for testing)."""
        self._connectors.clear()

# Global registry instance
connector_registry = ConnectorRegistry()

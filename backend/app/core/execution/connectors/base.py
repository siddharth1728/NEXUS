"""Base Connector abstraction for all NEXUS external integrations."""

from abc import ABC, abstractmethod

from app.models.enums import Capability
from app.schemas.connection import Connection, ConnectorHealth


class BaseConnector(ABC):
    """Base abstraction for all external integrations.

    A connector owns communication with an external system.
    Tools declare capabilities that rely on connectors.
    """

    @property
    @abstractmethod
    def provider(self) -> str:
        """The identifier of the provider (e.g., 'github')."""

    @property
    @abstractmethod
    def supported_capabilities(self) -> list[Capability]:
        """List of capabilities supported by this connector."""

    @abstractmethod
    async def check_health(self, connection: Connection) -> ConnectorHealth:
        """Check the health of a specific connection."""

    def get_credential_key(self, connection: Connection) -> str:
        """Get the secret store key for this connection.

        By default, format is: {provider}_{tenant_id}_TOKEN
        """
        return f"{self.provider.upper()}_{connection.tenant_id}_TOKEN"

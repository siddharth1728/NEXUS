"""NEXUS AI Provider Interfaces."""

from abc import ABC, abstractmethod

from app.core.ai.models import AIRequest, AIResponse


class AIProviderInterface(ABC):
    """Abstract interface for all AI provider adapters."""

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Return the normalized name of the provider."""
        pass

    @abstractmethod
    async def generate_content(self, request: AIRequest) -> AIResponse:
        """
        Generate content using the provider.

        Args:
            request: The normalized AI request.

        Returns:
            The normalized AI response.

        Raises:
            AIProviderError or its subclasses on failure.
            AIUnsupportedCapabilityError if the request requires unsupported features.
        """
        pass

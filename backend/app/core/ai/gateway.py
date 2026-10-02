"""NEXUS Provider-Agnostic AI Gateway."""

from app.core.ai.errors import AIProviderError
from app.core.ai.interfaces import AIProviderInterface
from app.core.ai.models import AIRequest, AIResponse
from app.core.ai.providers import (
    GeminiProvider,
    HuggingFaceProvider,
    MockAIProvider,
    OllamaProvider,
)
from app.core.config import get_settings


class AIGateway:
    """Entrypoint for all AI operations in NEXUS.

    Routes requests to the appropriate provider based on configuration,
    ensuring business logic remains completely decoupled from specific SDKs.
    """

    def __init__(self) -> None:
        self.settings = get_settings()
        self._providers: dict[str, AIProviderInterface] = {
            "gemini": GeminiProvider(),
            "huggingface": HuggingFaceProvider(),
            "ollama": OllamaProvider(),
            "mock": MockAIProvider(),
        }

    def _get_provider(self, provider_name: str | None = None) -> AIProviderInterface:
        """Resolve the provider implementation."""
        name = provider_name or self.settings.ai.default_provider
        provider = self._providers.get(name.lower())
        if not provider:
            raise AIProviderError(name, f"Provider '{name}' is not registered or supported.")
        return provider

    async def generate(self, request: AIRequest) -> AIResponse:
        """
        Execute an AI text generation request.

        Args:
            request: The normalized AI request parameters.

        Returns:
            The normalized AI response containing generated content and metadata.

        Raises:
            AIProviderError or its subclasses on failure.
        """
        provider = self._get_provider(request.provider)

        # Here we could inject observability hooks (e.g., logging request start with correlation ID)

        response = await provider.generate_content(request)

        # Here we could inject observability hooks (e.g., logging response success/latency)

        return response

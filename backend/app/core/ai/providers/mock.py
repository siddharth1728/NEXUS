"""Mock AI Provider for deterministic testing."""

from app.core.ai.errors import AIModelUnavailableError, AIProviderError
from app.core.ai.interfaces import AIProviderInterface
from app.core.ai.models import AIRequest, AIResponse


class MockAIProvider(AIProviderInterface):
    """Deterministic mock provider for CI and unit tests."""

    def __init__(self) -> None:
        self.should_fail = False
        self.canned_response = "Mock response"
        self.canned_latency = 10
        self.canned_structured = False

    @property
    def provider_name(self) -> str:
        return "mock"

    async def generate_content(self, request: AIRequest) -> AIResponse:
        if self.should_fail:
            raise AIProviderError(self.provider_name, "Simulated provider failure")

        if request.model == "invalid-model":
            raise AIModelUnavailableError(self.provider_name, "Simulated model unavailability")

        return AIResponse(
            content=self.canned_response,
            provider=self.provider_name,
            model=request.model,
            provider_request_id="mock-req-123",
            latency_ms=self.canned_latency,
            is_structured=self.canned_structured or request.require_structured_output,
            usage_metadata={"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15},
        )

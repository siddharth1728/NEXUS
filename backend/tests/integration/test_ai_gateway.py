"""Integration tests for AI Gateway."""

import pytest

from app.core.ai.errors import AIProviderError
from app.core.ai.gateway import AIGateway
from app.core.ai.models import AIRequest


@pytest.fixture
def gateway() -> AIGateway:
    return AIGateway()


@pytest.mark.asyncio
@pytest.mark.integration
async def test_gateway_routing_to_mock(gateway: AIGateway) -> None:
    request = AIRequest(provider="mock", model="test-model", prompt="Test prompt")

    response = await gateway.generate(request)
    assert response.provider == "mock"
    assert response.content == "Mock response"
    assert response.model == "test-model"


@pytest.mark.asyncio
@pytest.mark.integration
async def test_gateway_unsupported_provider(gateway: AIGateway) -> None:
    request = AIRequest(provider="unknown-provider", model="test-model", prompt="Test")

    with pytest.raises(AIProviderError, match="not registered or supported"):
        await gateway.generate(request)


@pytest.mark.asyncio
@pytest.mark.integration
async def test_gateway_fallback_to_default_provider(gateway: AIGateway) -> None:
    # Modify settings instance for the gateway temporarily
    gateway.settings.ai.default_provider = "mock"

    # Request without explicit provider
    AIRequest(provider="", model="test-model", prompt="Test default")

    # We patch _get_provider locally to simulate fallback if provider string is empty
    # Wait, the request model has provider as a required string.
    # The AIGateway uses `request.provider` strictly, but let's test `_get_provider(None)`

    provider = gateway._get_provider(None)
    assert provider.provider_name == "mock"

    provider = gateway._get_provider("")
    assert provider.provider_name == "mock"

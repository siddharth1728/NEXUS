"""Unit tests for AI Provider Adapters."""

from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from app.core.ai.errors import (
    AIAuthenticationError,
    AIProviderError,
    AIRateLimitError,
    AITimeoutError,
    AIUnsupportedCapabilityError,
)
from app.core.ai.models import AIRequest
from app.core.ai.providers.gemini import GeminiProvider
from app.core.ai.providers.huggingface import HuggingFaceProvider
from app.core.ai.providers.mock import MockAIProvider
from app.core.ai.providers.ollama import OllamaProvider


@pytest.fixture
def mock_request() -> AIRequest:
    return AIRequest(
        provider="mock",
        model="test-model",
        prompt="Hello world",
        temperature=0.7,
    )


@pytest.mark.asyncio
@pytest.mark.unit
async def test_mock_provider(mock_request: AIRequest) -> None:
    provider = MockAIProvider()
    response = await provider.generate_content(mock_request)
    assert response.provider == "mock"
    assert response.model == "test-model"
    assert response.content == "Mock response"
    assert response.latency_ms == 10


@pytest.mark.asyncio
@pytest.mark.unit
async def test_mock_provider_failures(mock_request: AIRequest) -> None:
    provider = MockAIProvider()
    provider.should_fail = True
    with pytest.raises(AIProviderError, match="Simulated provider failure"):
        await provider.generate_content(mock_request)


@pytest.mark.asyncio
@pytest.mark.unit
@patch("app.core.ai.providers.gemini.httpx.AsyncClient")
async def test_gemini_provider_success(
    mock_client_class: AsyncMock, mock_request: AIRequest
) -> None:
    mock_request.provider = "gemini"

    # Mock httpx client and response
    mock_client = AsyncMock()
    mock_client_class.return_value.__aenter__.return_value = mock_client

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "candidates": [{"content": {"parts": [{"text": "Gemini response"}]}}],
        "usageMetadata": {"totalTokenCount": 5},
    }
    mock_client.post.return_value = mock_response

    provider = GeminiProvider(api_key="fake-key")
    response = await provider.generate_content(mock_request)

    assert response.content == "Gemini response"
    assert response.provider == "gemini"
    assert response.usage_metadata == {"totalTokenCount": 5}

    # Verify client called correctly
    mock_client.post.assert_called_once()
    call_args = mock_client.post.call_args
    assert "fake-key" in call_args[0][0]
    assert call_args[1]["json"]["contents"][0]["parts"][0]["text"] == "Hello world"


@pytest.mark.asyncio
@pytest.mark.unit
@patch("app.core.ai.providers.gemini.httpx.AsyncClient")
async def test_gemini_provider_with_options(
    mock_client_class: AsyncMock, mock_request: AIRequest
) -> None:
    mock_request.provider = "gemini"
    mock_request.require_structured_output = True
    mock_request.system_instruction = "Sys instr"
    mock_request.temperature = 1.0

    mock_client = AsyncMock()
    mock_client_class.return_value.__aenter__.return_value = mock_client

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "candidates": [{"content": {"parts": [{"text": "Gemini response"}]}}],
    }
    mock_client.post.return_value = mock_response

    provider = GeminiProvider(api_key="fake-key")
    response = await provider.generate_content(mock_request)

    assert response.is_structured is True
    call_args = mock_client.post.call_args
    assert call_args[1]["json"]["systemInstruction"]["parts"][0]["text"] == "Sys instr"
    assert call_args[1]["json"]["generationConfig"]["temperature"] == 1.0
    assert call_args[1]["json"]["generationConfig"]["responseMimeType"] == "application/json"


@pytest.mark.asyncio
@pytest.mark.unit
@patch("app.core.ai.providers.gemini.httpx.AsyncClient")
async def test_gemini_provider_timeout(
    mock_client_class: AsyncMock, mock_request: AIRequest
) -> None:
    mock_request.provider = "gemini"

    mock_client = AsyncMock()
    mock_client_class.return_value.__aenter__.return_value = mock_client
    mock_client.post.side_effect = httpx.TimeoutException("Timeout")

    provider = GeminiProvider(api_key="fake")
    with pytest.raises(AITimeoutError):
        await provider.generate_content(mock_request)


@pytest.mark.asyncio
@pytest.mark.unit
@patch("app.core.ai.providers.huggingface.httpx.AsyncClient")
async def test_huggingface_provider_success(
    mock_client_class: AsyncMock, mock_request: AIRequest
) -> None:
    mock_request.provider = "huggingface"

    mock_client = AsyncMock()
    mock_client_class.return_value.__aenter__.return_value = mock_client

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = [{"generated_text": "HF response"}]
    mock_client.post.return_value = mock_response

    provider = HuggingFaceProvider(api_key="fake-hf-key")
    response = await provider.generate_content(mock_request)

    assert response.content == "HF response"
    assert response.provider == "huggingface"


@pytest.mark.asyncio
@pytest.mark.unit
async def test_huggingface_provider_structured_unsupported(mock_request: AIRequest) -> None:
    mock_request.provider = "huggingface"
    mock_request.require_structured_output = True

    provider = HuggingFaceProvider(api_key="fake")
    with pytest.raises(AIUnsupportedCapabilityError, match="require_structured_output"):
        await provider.generate_content(mock_request)


@pytest.mark.asyncio
@pytest.mark.unit
@patch("app.core.ai.providers.ollama.httpx.AsyncClient")
async def test_ollama_provider_success(
    mock_client_class: AsyncMock, mock_request: AIRequest
) -> None:
    mock_request.provider = "ollama"
    mock_request.require_structured_output = True

    mock_client = AsyncMock()
    mock_client_class.return_value.__aenter__.return_value = mock_client

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"response": '{"structured": true}', "eval_count": 42}
    mock_client.post.return_value = mock_response

    provider = OllamaProvider(host_url="http://fake:11434")
    response = await provider.generate_content(mock_request)

    assert response.content == '{"structured": true}'
    assert response.is_structured is True
    assert response.usage_metadata is not None
    assert response.usage_metadata["eval_count"] == 42


@pytest.mark.unit
def test_gemini_handle_errors() -> None:
    provider = GeminiProvider(api_key="fake")
    resp = MagicMock(status_code=401)
    with pytest.raises(AIAuthenticationError):
        provider._handle_errors(resp)

    resp.status_code = 429
    with pytest.raises(AIRateLimitError):
        provider._handle_errors(resp)

    resp.status_code = 500
    with pytest.raises(AIProviderError):
        provider._handle_errors(resp)


@pytest.mark.unit
def test_huggingface_handle_errors() -> None:
    provider = HuggingFaceProvider(api_key="fake")
    resp = MagicMock(status_code=401)
    with pytest.raises(AIAuthenticationError):
        provider._handle_errors(resp)

    resp.status_code = 429
    with pytest.raises(AIRateLimitError):
        provider._handle_errors(resp)

    resp.status_code = 503
    with pytest.raises(AIProviderError, match="loading"):
        provider._handle_errors(resp)

    resp.status_code = 500
    with pytest.raises(AIProviderError):
        provider._handle_errors(resp)


@pytest.mark.unit
def test_ollama_handle_errors() -> None:
    provider = OllamaProvider(host_url="http://fake")
    resp = MagicMock(status_code=404)
    with pytest.raises(AIProviderError, match="not found"):
        provider._handle_errors(resp)

    resp.status_code = 500
    with pytest.raises(AIProviderError):
        provider._handle_errors(resp)

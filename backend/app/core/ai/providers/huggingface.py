"""Hugging Face AI Provider Adapter."""

import json
import time
from typing import Any

import httpx

from app.core.ai.errors import (
    AIAuthenticationError,
    AIBadResponseError,
    AIProviderError,
    AIRateLimitError,
    AITimeoutError,
    AIUnsupportedCapabilityError,
)
from app.core.ai.interfaces import AIProviderInterface
from app.core.ai.models import AIRequest, AIResponse
from app.core.config import get_settings


class HuggingFaceProvider(AIProviderInterface):
    """Adapter for Hugging Face Serverless Inference API."""

    def __init__(self, api_key: str | None = None) -> None:
        self.api_key = api_key or get_settings().ai.huggingface_api_token
        self.base_url = "https://api-inference.huggingface.co/models"

    @property
    def provider_name(self) -> str:
        return "huggingface"

    async def generate_content(self, request: AIRequest) -> AIResponse:
        # HF Serverless often doesn't natively support structured output guarantees universally.
        if request.require_structured_output:
            # We explicitly fail if structured output is requested but not guaranteed by the abstraction
            # Note: TGI does support it via JSON grammar, but we restrict it for now to enforce safety.
            raise AIUnsupportedCapabilityError(self.provider_name, "require_structured_output")

        url = f"{self.base_url}/{request.model}"
        headers = {}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        # Assuming Text Generation API format
        prompt = request.prompt
        if request.system_instruction:
            prompt = f"{request.system_instruction}\n\n{prompt}"

        payload: dict[str, Any] = {"inputs": prompt, "parameters": {"return_full_text": False}}

        if request.temperature is not None:
            payload["parameters"]["temperature"] = request.temperature

        start_time = time.perf_counter()

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(url, headers=headers, json=payload)
        except httpx.TimeoutException as e:
            raise AITimeoutError(self.provider_name, "Hugging Face request timed out.") from e
        except httpx.RequestError as e:
            raise AIProviderError(self.provider_name, f"Network error: {str(e)}") from e

        latency_ms = int((time.perf_counter() - start_time) * 1000)

        self._handle_errors(response)

        try:
            data = response.json()
            if isinstance(data, list) and len(data) > 0 and "generated_text" in data[0]:
                content = data[0]["generated_text"]
            else:
                raise AIBadResponseError(self.provider_name, "Unexpected response format.")
        except (json.JSONDecodeError, KeyError) as e:
            raise AIBadResponseError(
                self.provider_name, "Malformed response from Hugging Face."
            ) from e

        return AIResponse(
            content=content,
            provider=self.provider_name,
            model=request.model,
            latency_ms=latency_ms,
        )

    def _handle_errors(self, response: httpx.Response) -> None:
        if response.status_code == 200:
            return

        status = response.status_code
        if status in (401, 403):
            raise AIAuthenticationError(
                self.provider_name, "Invalid Hugging Face API key or forbidden."
            )
        if status == 429:
            raise AIRateLimitError(self.provider_name, "Hugging Face rate limit exceeded.")

        # Model loading (503) is common on HF free tier
        if status == 503:
            raise AIProviderError(self.provider_name, "Hugging Face model is currently loading.")

        raise AIProviderError(
            self.provider_name, f"Hugging Face API returned status {status}: {response.text}"
        )

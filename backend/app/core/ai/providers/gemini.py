"""Gemini AI Provider Adapter."""

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
)
from app.core.ai.interfaces import AIProviderInterface
from app.core.ai.models import AIRequest, AIResponse
from app.core.config import get_settings


class GeminiProvider(AIProviderInterface):
    """Adapter for Google Gemini models via REST API."""

    def __init__(self, api_key: str | None = None) -> None:
        self.api_key = api_key or get_settings().ai.gemini_api_key
        self.base_url = "https://generativelanguage.googleapis.com/v1beta/models"

    @property
    def provider_name(self) -> str:
        return "gemini"

    async def generate_content(self, request: AIRequest) -> AIResponse:
        if not self.api_key:
            raise AIAuthenticationError(self.provider_name, "Gemini API key is not configured.")

        # Map to Gemini REST API format
        url = f"{self.base_url}/{request.model}:generateContent?key={self.api_key}"

        payload: dict[str, Any] = {"contents": [{"parts": [{"text": request.prompt}]}]}

        if request.system_instruction:
            payload["systemInstruction"] = {"parts": [{"text": request.system_instruction}]}

        generation_config: dict[str, Any] = {}
        if request.temperature is not None:
            generation_config["temperature"] = request.temperature
        if request.require_structured_output:
            generation_config["responseMimeType"] = "application/json"

        if generation_config:
            payload["generationConfig"] = generation_config

        start_time = time.perf_counter()

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(url, json=payload)
        except httpx.TimeoutException as e:
            raise AITimeoutError(self.provider_name, "Gemini request timed out.") from e
        except httpx.RequestError as e:
            raise AIProviderError(self.provider_name, f"Network error: {str(e)}") from e

        latency_ms = int((time.perf_counter() - start_time) * 1000)

        self._handle_errors(response)

        try:
            data = response.json()
            content = data["candidates"][0]["content"]["parts"][0]["text"]

            # Extract usage metadata if available
            usage = data.get("usageMetadata", {})
        except (KeyError, IndexError, json.JSONDecodeError) as e:
            raise AIBadResponseError(self.provider_name, "Malformed response from Gemini.") from e

        return AIResponse(
            content=content,
            provider=self.provider_name,
            model=request.model,
            latency_ms=latency_ms,
            usage_metadata=usage,
            is_structured=request.require_structured_output,
        )

    def _handle_errors(self, response: httpx.Response) -> None:
        """Map HTTP status codes to normalized AI errors."""
        if response.status_code == 200:
            return

        status = response.status_code
        if status in (401, 403):
            raise AIAuthenticationError(self.provider_name, "Invalid Gemini API key or forbidden.")
        if status == 429:
            raise AIRateLimitError(self.provider_name, "Gemini rate limit exceeded.")

        raise AIProviderError(
            self.provider_name, f"Gemini API returned status {status}: {response.text}"
        )

"""Ollama AI Provider Adapter."""

import json
import time
from typing import Any

import httpx

from app.core.ai.errors import (
    AIBadResponseError,
    AIProviderError,
    AITimeoutError,
)
from app.core.ai.interfaces import AIProviderInterface
from app.core.ai.models import AIRequest, AIResponse
from app.core.config import get_settings


class OllamaProvider(AIProviderInterface):
    """Adapter for local Ollama models."""

    def __init__(self, host_url: str | None = None) -> None:
        self.base_url = host_url or get_settings().ai.ollama_base_url

    @property
    def provider_name(self) -> str:
        return "ollama"

    async def generate_content(self, request: AIRequest) -> AIResponse:
        url = f"{self.base_url}/api/generate"

        payload: dict[str, Any] = {
            "model": request.model,
            "prompt": request.prompt,
            "stream": False,
        }

        if request.system_instruction:
            payload["system"] = request.system_instruction

        options: dict[str, Any] = {}
        if request.temperature is not None:
            options["temperature"] = request.temperature
        if options:
            payload["options"] = options

        if request.require_structured_output:
            payload["format"] = "json"

        start_time = time.perf_counter()

        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(url, json=payload)
        except httpx.TimeoutException as e:
            raise AITimeoutError(self.provider_name, "Ollama request timed out.") from e
        except httpx.RequestError as e:
            raise AIProviderError(
                self.provider_name, f"Network error or Ollama not running: {str(e)}"
            ) from e

        latency_ms = int((time.perf_counter() - start_time) * 1000)

        self._handle_errors(response)

        try:
            data = response.json()
            content = data["response"]

            usage = {
                "prompt_eval_count": data.get("prompt_eval_count", 0),
                "eval_count": data.get("eval_count", 0),
            }
        except (json.JSONDecodeError, KeyError) as e:
            raise AIBadResponseError(self.provider_name, "Malformed response from Ollama.") from e

        return AIResponse(
            content=content,
            provider=self.provider_name,
            model=request.model,
            latency_ms=latency_ms,
            usage_metadata=usage,
            is_structured=request.require_structured_output,
        )

    def _handle_errors(self, response: httpx.Response) -> None:
        if response.status_code == 200:
            return

        status = response.status_code
        if status == 404:
            raise AIProviderError(
                self.provider_name, "Model not found in Ollama. Please pull it first."
            )

        raise AIProviderError(
            self.provider_name, f"Ollama API returned status {status}: {response.text}"
        )

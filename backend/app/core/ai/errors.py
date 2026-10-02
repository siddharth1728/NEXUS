"""NEXUS AI Error Model."""

from typing import Any

from app.core.errors import AppError, DependencyUnavailableError


class AIProviderError(DependencyUnavailableError):
    """Base exception for all normalized AI provider errors."""

    def __init__(self, provider: str, message: str, details: dict[str, Any] | None = None) -> None:
        super().__init__(service_name=f"ai_provider_{provider}", message=message, details=details)


class AIAuthenticationError(AIProviderError):
    """Provider rejected credentials."""

    status_code = 502
    error_code = "AI_AUTHENTICATION_FAILED"


class AITimeoutError(AIProviderError):
    """Provider request timed out."""

    status_code = 504
    error_code = "AI_TIMEOUT"


class AIRateLimitError(AIProviderError):
    """Provider rate limit exceeded."""

    status_code = 429
    error_code = "AI_RATE_LIMIT_EXCEEDED"


class AIBadResponseError(AIProviderError):
    """Provider returned malformed or unexpected data."""

    status_code = 502
    error_code = "AI_BAD_RESPONSE"


class AIUnsupportedCapabilityError(AppError):
    """Requested capability is not supported by the provider/model."""

    status_code = 400
    error_code = "AI_UNSUPPORTED_CAPABILITY"

    def __init__(self, provider: str, capability: str) -> None:
        msg = f"Provider '{provider}' does not support capability '{capability}'."
        super().__init__(msg, details={"provider": provider, "capability": capability})


class AIModelUnavailableError(AIProviderError):
    """Requested model is unavailable or does not exist."""

    status_code = 502
    error_code = "AI_MODEL_UNAVAILABLE"

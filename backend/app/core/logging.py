"""NEXUS Structured Logging System.

Provides context-aware, structured logging with correlation IDs, log level controls,
and sensitive field redaction.
"""

import json
import logging
import sys
from contextvars import ContextVar
from datetime import UTC, datetime
from typing import Any

# Context variable for request correlation tracking
correlation_id_ctx: ContextVar[str | None] = ContextVar("correlation_id", default=None)

# Sensitive keys to redact from logs
SENSITIVE_KEYS = {
    "password",
    "secret",
    "token",
    "api_key",
    "authorization",
    "gemini_api_key",
    "huggingface_api_token",
    "app_secret_key",
}


def mask_sensitive_data(data: Any) -> Any:
    """Recursively mask sensitive values in nested dictionaries and lists."""
    if isinstance(data, dict):
        masked: dict[str, Any] = {}
        for k, v in data.items():
            if any(sens in k.lower() for sens in SENSITIVE_KEYS):
                masked[k] = "******"
            else:
                masked[k] = mask_sensitive_data(v)
        return masked
    elif isinstance(data, list):
        return [mask_sensitive_data(item) for item in data]
    return data


class StructuredLogFormatter(logging.Formatter):
    """Custom logging formatter supporting JSON and readable text with correlation IDs."""

    def __init__(self, use_json: bool = False) -> None:
        super().__init__()
        self.use_json = use_json

    def format(self, record: logging.LogRecord) -> str:
        correlation_id = correlation_id_ctx.get()
        timestamp = datetime.now(UTC).isoformat()

        if self.use_json:
            log_payload: dict[str, Any] = {
                "timestamp": timestamp,
                "level": record.levelname,
                "logger": record.name,
                "message": record.getMessage(),
                "correlation_id": correlation_id,
            }
            if record.exc_info:
                log_payload["exception"] = self.formatException(record.exc_info)
            if hasattr(record, "extra_fields") and isinstance(record.extra_fields, dict):
                log_payload.update(mask_sensitive_data(record.extra_fields))
            return json.dumps(log_payload)

        # Standard human-readable console format
        corr_str = f" [{correlation_id}]" if correlation_id else ""
        exc_str = f"\n{self.formatException(record.exc_info)}" if record.exc_info else ""
        return f"{timestamp} [{record.levelname:^7}] {record.name}{corr_str} - {record.getMessage()}{exc_str}"


def setup_logging(log_level: str = "INFO", use_json: bool = False) -> None:
    """Initialize root and application loggers with custom formatting."""
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    # Remove existing handlers to avoid duplicates
    for handler in list(root_logger.handlers):
        root_logger.removeHandler(handler)

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(StructuredLogFormatter(use_json=use_json))
    root_logger.addHandler(console_handler)

    # Tone down overly noisy third-party loggers
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("asyncio").setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """Return configured logger instance for a given module."""
    return logging.getLogger(f"nexus.{name}")

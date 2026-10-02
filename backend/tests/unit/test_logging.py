"""Unit tests for structured logging and sensitive data masking."""

import json
import logging

from app.core.logging import (
    StructuredLogFormatter,
    correlation_id_ctx,
    mask_sensitive_data,
    setup_logging,
)


def test_mask_sensitive_data() -> None:
    raw = {
        "user": "alice",
        "password": "supersecretpassword",
        "api_key": "xyz12345",
        "nested": {
            "token": "tok_abcdef",
            "safe_val": 42,
        },
        "list_data": [{"gemini_api_key": "gemini-sec"}, {"normal": "val"}],
    }

    masked = mask_sensitive_data(raw)
    assert masked["user"] == "alice"
    assert masked["password"] == "******"
    assert masked["api_key"] == "******"
    assert masked["nested"]["token"] == "******"
    assert masked["nested"]["safe_val"] == 42
    assert masked["list_data"][0]["gemini_api_key"] == "******"
    assert masked["list_data"][1]["normal"] == "val"


def test_structured_log_formatter_text() -> None:
    formatter = StructuredLogFormatter(use_json=False)
    record = logging.LogRecord(
        name="test_logger",
        level=logging.INFO,
        pathname="",
        lineno=0,
        msg="Test log message",
        args=(),
        exc_info=None,
    )

    token = correlation_id_ctx.set("test-corr-id-123")
    try:
        formatted = formatter.format(record)
        assert "[test-corr-id-123]" in formatted
        assert "Test log message" in formatted
    finally:
        correlation_id_ctx.reset(token)


def test_structured_log_formatter_json() -> None:
    formatter = StructuredLogFormatter(use_json=True)
    record = logging.LogRecord(
        name="test_json_logger",
        level=logging.ERROR,
        pathname="",
        lineno=0,
        msg="Database timeout",
        args=(),
        exc_info=None,
    )

    token = correlation_id_ctx.set("corr-json-789")
    try:
        formatted = formatter.format(record)
        data = json.loads(formatted)
        assert data["level"] == "ERROR"
        assert data["logger"] == "test_json_logger"
        assert data["message"] == "Database timeout"
        assert data["correlation_id"] == "corr-json-789"
    finally:
        correlation_id_ctx.reset(token)


def test_setup_logging() -> None:
    setup_logging(log_level="DEBUG", use_json=False)
    logger = logging.getLogger()
    assert logger.level == logging.DEBUG
    assert len(logger.handlers) == 1

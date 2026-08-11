"""
test_email_service.py
---------------------
Tests the email service provider abstractions.
Mocks out actual network calls to ensure isolation and speed.
"""

import pytest
import smtplib
from unittest.mock import patch, MagicMock

from app.services.email_service import send_password_reset_email
from app.core.config import settings

@pytest.fixture
def mock_settings(monkeypatch):
    """Provides a way to override settings during tests safely."""
    def _override(**kwargs):
        for k, v in kwargs.items():
            monkeypatch.setattr(settings, k, v)
    return _override


def test_send_stub(mock_settings, capsys):
    mock_settings(EMAIL_PROVIDER="stub")
    
    send_password_reset_email("test@example.com", "http://reset.link")
    
    captured = capsys.readouterr()
    assert "DEVELOPMENT EMAIL STUB" in captured.out
    assert "test@example.com" in captured.out
    assert "http://reset.link" in captured.out


@patch("httpx.post")
def test_send_sendgrid_success(mock_post, mock_settings):
    mock_settings(
        EMAIL_PROVIDER="sendgrid",
        EMAIL_API_KEY="SG.fake_key"
    )
    
    # Mock a successful response
    mock_resp = MagicMock()
    mock_resp.raise_for_status.return_value = None
    mock_post.return_value = mock_resp
    
    send_password_reset_email("test@example.com", "http://reset.link")
    
    mock_post.assert_called_once()
    args, kwargs = mock_post.call_args
    assert args[0] == "https://api.sendgrid.com/v3/mail/send"
    assert kwargs["headers"]["Authorization"] == "Bearer SG.fake_key"
    
    # Assert body structure
    payload = kwargs["json"]
    assert payload["personalizations"][0]["to"][0]["email"] == "test@example.com"
    assert "http://reset.link" in payload["content"][0]["value"] # Plain text
    assert "http://reset.link" in payload["content"][1]["value"] # HTML


@patch("smtplib.SMTP")
def test_send_smtp_success(mock_smtp_class, mock_settings):
    mock_settings(
        EMAIL_PROVIDER="smtp",
        SMTP_HOST="smtp.test.com",
        SMTP_PORT=587,
        SMTP_USERNAME="user",
        SMTP_PASSWORD="password",
        SMTP_USE_TLS=True,
        EMAIL_FROM="from@test.com"
    )
    
    # Setup mock SMTP instance
    mock_smtp_instance = MagicMock()
    mock_smtp_class.return_value.__enter__.return_value = mock_smtp_instance
    
    send_password_reset_email("test@example.com", "http://reset.link")
    
    mock_smtp_class.assert_called_once_with("smtp.test.com", 587, timeout=10)
    mock_smtp_instance.starttls.assert_called_once()
    mock_smtp_instance.login.assert_called_once_with("user", "password")
    mock_smtp_instance.sendmail.assert_called_once()
    
    # Verify sent mail
    args, _ = mock_smtp_instance.sendmail.call_args
    assert args[0] == "from@test.com"
    assert args[1] == ["test@example.com"]
    assert "http://reset.link" in args[2]


def test_invalid_provider(mock_settings):
    mock_settings(EMAIL_PROVIDER="invalid_provider")
    
    with pytest.raises(RuntimeError, match="Unknown EMAIL_PROVIDER 'invalid_provider'"):
        send_password_reset_email("test@example.com", "http://reset.link")

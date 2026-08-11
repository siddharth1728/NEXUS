"""
email_service.py
----------------
Password-reset email delivery abstraction for NEXUS.

Supported providers (configured via EMAIL_PROVIDER env var):
  stub      -- Development only. Prints the reset URL to stdout.
               Raises at startup if used in production (enforced in config.py).
  sendgrid  -- Sends via the SendGrid v3 Mail Send API (httpx; no SDK needed).
  smtp      -- Sends via any SMTP relay using Python stdlib smtplib.

Security invariants:
  * Credentials (EMAIL_API_KEY, SMTP_PASSWORD) are NEVER logged.
  * reset_url is NEVER logged in production mode.
  * Only status codes and provider names appear in error logs.
"""

import logging
import smtplib
import ssl
import textwrap
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from app.core.config import settings

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Email body builders
# ---------------------------------------------------------------------------

def _build_plain_text(reset_url: str) -> str:
    return textwrap.dedent(f"""\
        NEXUS -- Password Reset Request
        ==============================

        Someone requested a password reset for your NEXUS account.
        If this was you, use the link below to set a new password:

        {reset_url}

        This link expires in 30 minutes.

        If you did not request a password reset, you can safely ignore this
        email. Your password has NOT been changed.

        -- The NEXUS Team
    """)


def _build_html(reset_url: str) -> str:
    return (
        '<!DOCTYPE html><html lang="en"><head>'
        '<meta charset="UTF-8">'
        '<meta name="viewport" content="width=device-width, initial-scale=1.0">'
        '<title>Reset your NEXUS password</title>'
        "<style>"
        "body{font-family:-apple-system,BlinkMacSystemFont,'Inter','Segoe UI',sans-serif;"
        "background:#F3F1EB;margin:0;padding:40px 16px}"
        ".container{background:#FAF9F6;border-radius:12px;max-width:560px;"
        "margin:0 auto;padding:40px;border:1px solid #E8E4DC}"
        ".brand{font-size:13px;font-weight:700;letter-spacing:.12em;"
        "text-transform:uppercase;color:#6B6560;margin-bottom:32px}"
        "h1{font-size:22px;font-weight:600;color:#171717;letter-spacing:-.3px;margin:0 0 16px}"
        "p{font-size:15px;color:#4A4540;line-height:1.6;margin:0 0 20px}"
        ".btn{display:inline-block;background:#171717;color:#FAF9F6;"
        "text-decoration:none;padding:12px 24px;border-radius:8px;"
        "font-size:14px;font-weight:600;margin:8px 0 24px}"
        ".expiry{font-size:13px;color:#6B6560;background:#F3F1EB;"
        "border-radius:6px;padding:12px 16px}"
        ".footer{font-size:12px;color:#9E9890;margin-top:32px;"
        "padding-top:24px;border-top:1px solid #E8E4DC}"
        ".url-fallback{word-break:break-all;font-size:12px;color:#6B6560}"
        "</style></head><body>"
        '<div class="container">'
        '<div class="brand">NEXUS Engineering OS</div>'
        "<h1>Reset your password</h1>"
        "<p>Someone requested a password reset for your NEXUS account. "
        "If this was you, click the button below to set a new password.</p>"
        f'<a class="btn" href="{reset_url}">Reset my password</a>'
        '<div class="expiry">This link expires in <strong>30 minutes</strong>.</div>'
        '<p style="margin-top:20px;font-size:13px;color:#6B6560">'
        "If the button doesn't work, copy and paste this link into your browser:</p>"
        f'<p class="url-fallback">{reset_url}</p>'
        '<div class="footer">If you did not request a password reset, you can safely '
        "ignore this email. Your password has <strong>not</strong> been changed.</div>"
        "</div></body></html>"
    )


# ---------------------------------------------------------------------------
# Provider implementations
# ---------------------------------------------------------------------------

def _send_stub(email: str, reset_url: str) -> None:
    """Development stub: prints reset info to stdout. MUST NOT run in production."""
    print("=" * 44)
    print("NEXUS -- DEVELOPMENT EMAIL STUB")
    print(f"To:         {email}")
    print("Subject:    Reset your NEXUS password")
    print(f"Reset Link: {reset_url}")
    print("Expires:    30 minutes")
    print("=" * 44)


def _send_sendgrid(email: str, reset_url: str) -> None:
    """Send via SendGrid v3 Mail Send API (httpx; no SDK required)."""
    import httpx

    api_key = settings.EMAIL_API_KEY
    if not api_key:
        raise RuntimeError("EMAIL_API_KEY is required for EMAIL_PROVIDER=sendgrid")

    payload = {
        "personalizations": [{"to": [{"email": email}]}],
        "from": {"email": settings.EMAIL_FROM, "name": "NEXUS"},
        "subject": "Reset your NEXUS password",
        "content": [
            {"type": "text/plain", "value": _build_plain_text(reset_url)},
            {"type": "text/html",  "value": _build_html(reset_url)},
        ],
    }

    try:
        resp = httpx.post(
            "https://api.sendgrid.com/v3/mail/send",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json=payload,
            timeout=10.0,
        )
        resp.raise_for_status()
        logger.info("Password reset email dispatched via SendGrid to %s", email)
    except httpx.HTTPStatusError as exc:
        # Log only status code -- NEVER log the API key or response body
        status = exc.response.status_code
        logger.error("SendGrid delivery failed for %s: HTTP %s", email, status)
        raise RuntimeError(f"Email delivery failed (SendGrid HTTP {status})") from exc
    except httpx.RequestError as exc:
        logger.error("SendGrid network error for %s: %s", email, type(exc).__name__)
        raise RuntimeError("Email delivery failed (network error)") from exc


def _send_smtp(email: str, reset_url: str) -> None:
    """Send via an SMTP relay (TLS, port 587 by default)."""
    host = settings.SMTP_HOST
    port = settings.SMTP_PORT
    username = settings.SMTP_USERNAME
    password = settings.SMTP_PASSWORD
    use_tls = settings.SMTP_USE_TLS

    if not host or not username or not password:
        raise RuntimeError(
            "SMTP_HOST, SMTP_USERNAME, and SMTP_PASSWORD are required for EMAIL_PROVIDER=smtp"
        )

    msg = MIMEMultipart("alternative")
    msg["Subject"] = "Reset your NEXUS password"
    msg["From"] = settings.EMAIL_FROM
    msg["To"] = email
    msg.attach(MIMEText(_build_plain_text(reset_url), "plain"))
    msg.attach(MIMEText(_build_html(reset_url), "html"))

    try:
        context = ssl.create_default_context()
        with smtplib.SMTP(host, port, timeout=10) as server:
            if use_tls:
                server.starttls(context=context)
            server.login(username, password)
            server.sendmail(settings.EMAIL_FROM, [email], msg.as_string())
        logger.info("Password reset email dispatched via SMTP to %s", email)
    except smtplib.SMTPAuthenticationError:
        # Auth failure -- do NOT log credentials
        logger.error(
            "SMTP authentication failed for %s (check SMTP_USERNAME/SMTP_PASSWORD)", email
        )
        raise RuntimeError("Email delivery failed (SMTP authentication error)") from None
    except smtplib.SMTPException as exc:
        logger.error("SMTP delivery failed for %s: %s", email, type(exc).__name__)
        raise RuntimeError("Email delivery failed (SMTP error)") from exc
    except OSError as exc:
        logger.error("SMTP connection error for %s: %s", email, type(exc).__name__)
        raise RuntimeError("Email delivery failed (connection error)") from exc


# ---------------------------------------------------------------------------
# Public interface
# ---------------------------------------------------------------------------

def send_password_reset_email(email: str, reset_url: str) -> None:
    """
    Dispatch a password reset email using the configured EMAIL_PROVIDER.

    The reset_url contains the raw (pre-hash) token and MUST NEVER be logged
    in production. This invariant is upheld by all provider implementations.
    """
    provider = settings.EMAIL_PROVIDER

    if provider == "stub":
        _send_stub(email, reset_url)
    elif provider == "sendgrid":
        _send_sendgrid(email, reset_url)
    elif provider == "smtp":
        _send_smtp(email, reset_url)
    else:
        raise RuntimeError(
            f"Unknown EMAIL_PROVIDER '{provider}'. "
            "Valid values: 'stub', 'sendgrid', 'smtp'."
        )

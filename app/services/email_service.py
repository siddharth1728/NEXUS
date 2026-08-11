import logging
from app.core.config import settings

logger = logging.getLogger(__name__)

def send_password_reset_email(email: str, reset_url: str):
    """
    Abstracts sending a password reset email.
    In development mode, securely logs the URL.
    In production, this should integrate with a transactional email provider (SendGrid, Postmark, AWS SES, etc).
    """
    if settings.ENVIRONMENT == "development":
        print(f"========== DEVELOPMENT MODE ==========")
        print(f"Password reset requested for: {email}")
        print(f"Reset Link: {reset_url}")
        print(f"======================================")
    else:
        # TODO: Implement production email sending integration
        # CRITICAL: Do NOT log the raw reset_url in production!
        logger.info(f"Password reset email sent to {email}")

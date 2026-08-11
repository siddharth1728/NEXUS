"""
test_production_config.py
--------------------------
Tests that the Settings model's production-mode validator:
  1. Rejects the known development secret key sentinel.
  2. Rejects a secret key shorter than 32 characters.
  3. Rejects EMAIL_PROVIDER='stub' in production.
  4. Rejects EMAIL_PROVIDER='sendgrid' without EMAIL_API_KEY.
  5. Rejects EMAIL_PROVIDER='smtp' without SMTP credentials.
  6. Accepts a properly configured production Settings object.
  7. Is completely lenient in development mode.
  8. Never exposes the secret via the API.
"""

import pytest
from pydantic import ValidationError

from app.core.config import _DEV_SECRET_SENTINEL


# ── Helpers ───────────────────────────────────────────────────────────────────

def make_settings(**overrides):
    """
    Build a Settings object from an environment-variable dict.
    We bypass the .env file by using model_validate with a dict.
    """
    from app.core.config import Settings

    base = {
        "DATABASE_URL": "postgresql+psycopg://u:p@localhost/nexus_dev",
        "TEST_DATABASE_URL": "postgresql+psycopg://u:p@localhost/nexus_test",
        "SECRET_KEY": "a" * 32,          # valid default
        "ENVIRONMENT": "development",
        "EMAIL_PROVIDER": "stub",
        "EMAIL_FROM": "noreply@nexus.local",
    }
    base.update(overrides)
    return Settings.model_validate(base)


# ── BLOCKER 1: SECRET_KEY validation ─────────────────────────────────────────

class TestSecretKeyValidation:

    def test_dev_mode_accepts_dev_sentinel(self):
        """Development mode should NOT raise even with the dev placeholder."""
        s = make_settings(
            SECRET_KEY=_DEV_SECRET_SENTINEL,
            ENVIRONMENT="development",
        )
        assert s.SECRET_KEY == _DEV_SECRET_SENTINEL

    def test_production_rejects_dev_sentinel(self):
        """Production must refuse the known dev placeholder secret."""
        with pytest.raises(ValidationError) as exc_info:
            make_settings(
                SECRET_KEY=_DEV_SECRET_SENTINEL,
                ENVIRONMENT="production",
                EMAIL_PROVIDER="sendgrid",
                EMAIL_API_KEY="SG.test_key_for_validation",
            )
        errors = str(exc_info.value)
        assert "dev" in errors.lower() or "placeholder" in errors.lower() or "development" in errors.lower()

    def test_production_rejects_short_secret(self):
        """Production must reject secrets shorter than 32 characters."""
        with pytest.raises(ValidationError) as exc_info:
            make_settings(
                SECRET_KEY="tooshort",
                ENVIRONMENT="production",
                EMAIL_PROVIDER="sendgrid",
                EMAIL_API_KEY="SG.test_key_for_validation",
            )
        assert "short" in str(exc_info.value).lower() or "32" in str(exc_info.value)

    def test_production_accepts_strong_secret(self):
        """Production must accept a 64-character hex secret (typical openssl output)."""
        strong_key = "a" * 64
        s = make_settings(
            SECRET_KEY=strong_key,
            ENVIRONMENT="production",
            EMAIL_PROVIDER="sendgrid",
            EMAIL_API_KEY="SG.test_key_for_validation",
        )
        assert s.SECRET_KEY == strong_key

    def test_dev_mode_accepts_short_secret(self):
        """Development mode should not reject short secrets (to not break quick local setups)."""
        s = make_settings(SECRET_KEY="shortkey", ENVIRONMENT="development")
        assert s.SECRET_KEY == "shortkey"

    def test_sentinel_value_is_documented(self):
        """The sentinel value matches what ships in .env.example."""
        assert _DEV_SECRET_SENTINEL == "dev_secret_key_change_me_in_production"


# ── BLOCKER 2: Email provider validation ──────────────────────────────────────

class TestEmailProviderValidation:

    def test_production_rejects_stub_provider(self):
        """Production must refuse EMAIL_PROVIDER='stub'."""
        with pytest.raises(ValidationError) as exc_info:
            make_settings(
                SECRET_KEY="a" * 64,
                ENVIRONMENT="production",
                EMAIL_PROVIDER="stub",
            )
        assert "stub" in str(exc_info.value).lower()

    def test_production_rejects_sendgrid_without_api_key(self):
        """Production with sendgrid must require EMAIL_API_KEY."""
        with pytest.raises(ValidationError) as exc_info:
            make_settings(
                SECRET_KEY="a" * 64,
                ENVIRONMENT="production",
                EMAIL_PROVIDER="sendgrid",
                EMAIL_API_KEY=None,
            )
        assert "sendgrid" in str(exc_info.value).lower() or "api_key" in str(exc_info.value).lower()

    def test_production_rejects_smtp_without_host(self):
        """Production with smtp must require SMTP_HOST."""
        with pytest.raises(ValidationError) as exc_info:
            make_settings(
                SECRET_KEY="a" * 64,
                ENVIRONMENT="production",
                EMAIL_PROVIDER="smtp",
                SMTP_HOST=None,
                SMTP_USERNAME="user",
                SMTP_PASSWORD="pass",
            )
        assert "smtp" in str(exc_info.value).lower()

    def test_production_rejects_smtp_without_credentials(self):
        """Production with smtp must require SMTP_USERNAME and SMTP_PASSWORD."""
        with pytest.raises(ValidationError) as exc_info:
            make_settings(
                SECRET_KEY="a" * 64,
                ENVIRONMENT="production",
                EMAIL_PROVIDER="smtp",
                SMTP_HOST="smtp.example.com",
                SMTP_USERNAME=None,
                SMTP_PASSWORD=None,
            )
        assert "smtp" in str(exc_info.value).lower()

    def test_production_accepts_sendgrid_with_api_key(self):
        """Production with sendgrid + API key must succeed."""
        s = make_settings(
            SECRET_KEY="a" * 64,
            ENVIRONMENT="production",
            EMAIL_PROVIDER="sendgrid",
            EMAIL_API_KEY="SG.valid_key_123",
        )
        assert s.EMAIL_PROVIDER == "sendgrid"
        assert s.EMAIL_API_KEY == "SG.valid_key_123"

    def test_production_accepts_smtp_with_credentials(self):
        """Production with smtp + full credentials must succeed."""
        s = make_settings(
            SECRET_KEY="a" * 64,
            ENVIRONMENT="production",
            EMAIL_PROVIDER="smtp",
            SMTP_HOST="smtp.example.com",
            SMTP_USERNAME="user@example.com",
            SMTP_PASSWORD="s3cur3!",
        )
        assert s.EMAIL_PROVIDER == "smtp"
        assert s.SMTP_HOST == "smtp.example.com"

    def test_dev_mode_accepts_stub_provider(self):
        """Development mode must accept EMAIL_PROVIDER='stub' (the default)."""
        s = make_settings(ENVIRONMENT="development", EMAIL_PROVIDER="stub")
        assert s.EMAIL_PROVIDER == "stub"

    def test_dev_mode_accepts_sendgrid_without_api_key(self):
        """Development mode should not require EMAIL_API_KEY even for sendgrid."""
        s = make_settings(
            ENVIRONMENT="development",
            EMAIL_PROVIDER="sendgrid",
            EMAIL_API_KEY=None,
        )
        assert s.EMAIL_PROVIDER == "sendgrid"


# ── BLOCKER 1+2: Secret never exposed through API ────────────────────────────

class TestSecretNeverExposed:

    def test_secret_not_in_profile_api(self, auth_client):
        """GET /api/profile must not return the SECRET_KEY."""
        resp = auth_client.get("/api/profile")
        assert resp.status_code == 200
        body = resp.text
        from app.core.config import settings as real_settings
        assert real_settings.SECRET_KEY not in body

    def test_secret_not_in_me_api(self, auth_client):
        """GET /api/auth/me must not return the SECRET_KEY."""
        resp = auth_client.get("/api/auth/me")
        assert resp.status_code == 200
        body = resp.text
        from app.core.config import settings as real_settings
        assert real_settings.SECRET_KEY not in body

    def test_dev_sentinel_not_in_health(self, client):
        """GET /health (if any) must not echo back the secret."""
        resp = client.get("/health")
        # May return 404 or 200 depending on the app — either way, no secret
        assert _DEV_SECRET_SENTINEL not in resp.text

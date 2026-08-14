from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import model_validator
from typing import Optional

# The exact placeholder that ships in .env.example / development.
# If this string is detected while ENVIRONMENT=production, startup is aborted.
_DEV_SECRET_SENTINEL = "dev_secret_key_change_me_in_production"

class Settings(BaseSettings):
    DATABASE_URL: str = "sqlite:////tmp/nexus.db"
    TEST_DATABASE_URL: str = "sqlite:///./test_nexus.db"
    SECRET_KEY: str = "dev_secret_key_change_me_in_production_min_32_bytes_nexus"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    ENVIRONMENT: str = "development"
    GITHUB_TOKEN: Optional[str] = None
    APP_BASE_URL: str = "http://localhost:8000"

    # ── Email provider ────────────────────────────────────────────────────
    # EMAIL_PROVIDER: "stub" (dev-only stdout), "sendgrid", or "smtp"
    EMAIL_PROVIDER: str = "stub"
    EMAIL_FROM: str = "noreply@nexus.local"
    EMAIL_API_KEY: Optional[str] = None       # SendGrid API key (production)

    # SMTP fields (used when EMAIL_PROVIDER=smtp)
    SMTP_HOST: Optional[str] = None
    SMTP_PORT: int = 587
    SMTP_USERNAME: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    SMTP_USE_TLS: bool = True

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @model_validator(mode="after")
    def _validate_production_security(self) -> "Settings":
        """
        Fail fast when running in production with insecure or missing configuration.

        Rules:
          1. SECRET_KEY must not be the known development placeholder.
          2. SECRET_KEY must be at least 32 characters (sufficient entropy for HS256).
          3. EMAIL_PROVIDER must not be "stub" in production.
          4. If EMAIL_PROVIDER=sendgrid, EMAIL_API_KEY must be set.
          5. If EMAIL_PROVIDER=smtp, SMTP_HOST and SMTP_USERNAME and SMTP_PASSWORD must be set.
        """
        is_production = self.ENVIRONMENT == "production"

        if is_production:
            # Rule 1: Reject the known dev sentinel
            if self.SECRET_KEY == _DEV_SECRET_SENTINEL:
                raise ValueError(
                    "SECURITY: SECRET_KEY is set to the development placeholder. "
                    "Generate a strong key with: openssl rand -hex 32"
                )

            # Rule 2: Minimum length guard (HS256 requires ≥ 256-bit = 32 bytes)
            if len(self.SECRET_KEY) < 32:
                raise ValueError(
                    "SECURITY: SECRET_KEY is too short for production. "
                    "Use a value of at least 32 characters."
                )

            # Rule 3: Disallow stub email provider
            if self.EMAIL_PROVIDER == "stub":
                raise ValueError(
                    "SECURITY: EMAIL_PROVIDER='stub' cannot be used in production. "
                    "Set EMAIL_PROVIDER to 'sendgrid' or 'smtp'."
                )

            # Rule 4: SendGrid requires API key
            if self.EMAIL_PROVIDER == "sendgrid" and not self.EMAIL_API_KEY:
                raise ValueError(
                    "SECURITY: EMAIL_PROVIDER='sendgrid' requires EMAIL_API_KEY to be set."
                )

            # Rule 5: SMTP requires connection details
            if self.EMAIL_PROVIDER == "smtp":
                missing = [
                    f for f in ["SMTP_HOST", "SMTP_USERNAME", "SMTP_PASSWORD"]
                    if not getattr(self, f)
                ]
                if missing:
                    raise ValueError(
                        f"SECURITY: EMAIL_PROVIDER='smtp' requires: {', '.join(missing)}"
                    )

        return self


settings = Settings()

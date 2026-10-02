"""SecretStore — explicit secret boundary for NEXUS credentials.

Secrets are NEVER stored in the primary database, Action records,
ExecutionRecord parameters, logs, or API responses.
"""

import os


class SecretStore:
    """Controlled credential store.

    For local development and tests, secrets are held in-memory and/or
    read from environment variables. Do not use a real secret manager until Phase 04+.
    """

    def __init__(self) -> None:
        self._mock_store: dict[str, str] = {}

    def get_secret(self, key: str) -> str | None:
        """Retrieve a secret by key. Never log the returned value."""
        if key in self._mock_store:
            return self._mock_store[key]
        return os.environ.get(key)

    def set_mock_secret(self, key: str, value: str) -> None:
        """Register a secret for testing only."""
        self._mock_store[key] = value

    def clear_mock_secrets(self) -> None:
        """Remove all mock secrets (use in test teardown)."""
        self._mock_store.clear()


# Module-level singleton — import this, do not instantiate SecretStore elsewhere.
secret_store = SecretStore()

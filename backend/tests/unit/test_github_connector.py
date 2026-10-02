"""Unit tests for the GitHubConnector."""

import uuid
from datetime import UTC, datetime
from typing import Any, Generator
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.core.errors import NotFoundError, ValidationError
from app.core.execution.connectors.github import GitHubConnector, GitHubError
from app.core.secrets import secret_store
from app.models.enums import Capability
from app.schemas.connection import Connection, ConnectionStatus


@pytest.fixture
def connection() -> Connection:
    now = datetime.now(UTC)
    return Connection(
        id=str(uuid.uuid4()),
        tenant_id="test-tenant",
        provider="github",
        status=ConnectionStatus.AVAILABLE,
        created_at=now,
        updated_at=now,
    )


@pytest.fixture
def connector() -> GitHubConnector:
    return GitHubConnector()


@pytest.fixture(autouse=True)
def setup_secrets() -> Generator[None, None, None]:
    secret_store.set_mock_secret("GITHUB_test-tenant_TOKEN", "mock-token-123")
    yield
    secret_store.clear_mock_secrets()


@pytest.mark.asyncio
async def test_connector_properties(connector: GitHubConnector) -> None:
    assert connector.provider == "github"
    assert Capability.GITHUB_REPOSITORY_READ in connector.supported_capabilities
    assert Capability.GITHUB_ISSUE_READ in connector.supported_capabilities
    assert Capability.GITHUB_ISSUE_CREATE in connector.supported_capabilities
    assert Capability.GITHUB_ISSUE_COMMENT_CREATE in connector.supported_capabilities


@pytest.mark.asyncio
async def test_health_check_success(connector: GitHubConnector, connection: Connection) -> None:
    with patch("httpx.AsyncClient.request", new_callable=AsyncMock) as mock_request:
        mock_response = MagicMock()
        mock_response.is_success = True
        mock_response.status_code = 200
        mock_response.json.return_value = {}
        mock_request.return_value = mock_response

        health = await connector.check_health(connection)

        assert health.status == ConnectionStatus.AVAILABLE
        assert health.provider == "github"


@pytest.mark.asyncio
async def test_health_check_missing_token(connector: GitHubConnector, connection: Connection) -> None:
    secret_store.clear_mock_secrets()

    health = await connector.check_health(connection)

    assert health.status == ConnectionStatus.AUTHENTICATION_REQUIRED
    assert health.message == "Missing credentials"


@pytest.mark.asyncio
async def test_health_check_invalid_token(connector: GitHubConnector, connection: Connection) -> None:
    with patch("httpx.AsyncClient.request", new_callable=AsyncMock) as mock_request:
        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_request.return_value = mock_response

        health = await connector.check_health(connection)

        assert health.status == ConnectionStatus.AUTHENTICATION_REQUIRED
        assert health.message is not None
        assert "credentials" in health.message


@pytest.mark.asyncio
async def test_read_repository_success(connector: GitHubConnector, connection: Connection) -> None:
    with patch("httpx.AsyncClient.request", new_callable=AsyncMock) as mock_request:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.is_success = True
        mock_response.json.return_value = {
            "id": 12345,
            "html_url": "https://github.com/owner/repo",
            "visibility": "public",
            "default_branch": "main",
        }
        mock_request.return_value = mock_response

        result = await connector.read_repository(connection, "owner", "repo")

        assert result["resource_type"] == "repository"
        assert result["resource_id"] == "12345"
        assert result["url"] == "https://github.com/owner/repo"


@pytest.mark.asyncio
async def test_read_repository_not_found(connector: GitHubConnector, connection: Connection) -> None:
    with patch("httpx.AsyncClient.request", new_callable=AsyncMock) as mock_request:
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_request.return_value = mock_response

        with pytest.raises(NotFoundError, match="not found"):
            await connector.read_repository(connection, "owner", "repo")


@pytest.mark.asyncio
async def test_error_normalization_rate_limit(connector: GitHubConnector, connection: Connection) -> None:
    with patch("httpx.AsyncClient.request", new_callable=AsyncMock) as mock_request:
        mock_response = MagicMock()
        mock_response.status_code = 403
        mock_response.text = "API rate limit exceeded"
        mock_request.return_value = mock_response
        with pytest.raises(GitHubError, match="rate limit"):
            await connector.read_repository(connection, "owner", "repo")


@pytest.mark.asyncio
async def test_error_normalization_validation(connector: GitHubConnector, connection: Connection) -> None:
    with patch("httpx.AsyncClient.request", new_callable=AsyncMock) as mock_request:
        mock_response = MagicMock()
        mock_response.status_code = 422
        mock_response.text = "Validation failed"
        mock_request.return_value = mock_response
        with pytest.raises(ValidationError, match="validation error"):
            await connector.read_repository(connection, "owner", "repo")


@pytest.mark.asyncio
async def test_create_issue_success(connector: GitHubConnector, connection: Connection) -> None:
    with patch("httpx.AsyncClient.request", new_callable=AsyncMock) as mock_request:
        mock_response = MagicMock()
        mock_response.status_code = 201
        mock_response.is_success = True
        mock_response.json.return_value = {
            "id": 54321,
            "number": 42,
            "title": "Bug fix",
            "html_url": "https://github.com/owner/repo/issues/42",
        }
        mock_request.return_value = mock_response

        result = await connector.create_issue(connection, "owner", "repo", "Bug fix", "Description")

        assert result["resource_type"] == "issue"
        assert result["issue_number"] == 42
        assert result["title"] == "Bug fix"


@pytest.mark.asyncio
async def test_create_comment_success(connector: GitHubConnector, connection: Connection) -> None:
    with patch("httpx.AsyncClient.request", new_callable=AsyncMock) as mock_request:
        mock_response = MagicMock()
        mock_response.status_code = 201
        mock_response.is_success = True
        mock_response.json.return_value = {
            "id": 99999,
            "html_url": "https://github.com/owner/repo/issues/42#issuecomment-99999",
        }
        mock_request.return_value = mock_response

        result = await connector.create_issue_comment(connection, "owner", "repo", 42, "LGTM!")

        assert result["resource_type"] == "issue_comment"
        assert result["resource_id"] == "99999"
        assert result["issue_number"] == 42


@pytest.mark.asyncio
async def test_connection_failure(connector: GitHubConnector, connection: Connection) -> None:
    with patch("httpx.AsyncClient.request", new_callable=AsyncMock) as mock_request:
        import httpx as _httpx
        mock_request.side_effect = _httpx.ConnectError("Connection refused")

        with pytest.raises(GitHubError, match="connection failure"):
            await connector.read_repository(connection, "owner", "repo")


@pytest.mark.asyncio
async def test_upstream_failure(connector: GitHubConnector, connection: Connection) -> None:
    with patch("httpx.AsyncClient.request", new_callable=AsyncMock) as mock_request:
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.is_success = False
        mock_request.return_value = mock_response

        with pytest.raises(GitHubError, match="upstream failure"):
            await connector.read_repository(connection, "owner", "repo")


@pytest.mark.asyncio
async def test_cross_tenant_credential_isolation(connector: GitHubConnector) -> None:
    """Tenant A cannot use a connection token belonging to Tenant B."""
    now = datetime.now(UTC)
    # Only Tenant B has a token registered
    secret_store.set_mock_secret("GITHUB_tenant-b_TOKEN", "tenant-b-secret")

    # Tenant A connection — should find no token
    conn_a = Connection(
        id="conn-a",
        tenant_id="tenant-a",
        provider="github",
        status=ConnectionStatus.AVAILABLE,
        created_at=now,
        updated_at=now,
    )

    health = await connector.check_health(conn_a)
    assert health.status == ConnectionStatus.AUTHENTICATION_REQUIRED


@pytest.mark.asyncio
async def test_credential_key_format(connector: GitHubConnector, connection: Connection) -> None:
    """The credential key must embed the tenant_id, not a static value."""
    key = connector.get_credential_key(connection)
    assert "test-tenant" in key
    assert "GITHUB" in key
    assert "TOKEN" in key


def test_connector_registry() -> None:
    from app.core.execution.connectors.registry import ConnectorRegistry

    registry = ConnectorRegistry()
    c = GitHubConnector()
    registry.register(c)

    assert registry.get("github") is c
    assert len(registry.list_all()) == 1

    registry.clear()
    assert registry.get("github") is None

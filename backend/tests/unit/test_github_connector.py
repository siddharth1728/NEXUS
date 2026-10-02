import uuid
from datetime import UTC, datetime
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
        updated_at=now
    )


@pytest.fixture
def connector() -> GitHubConnector:
    return GitHubConnector()


@pytest.fixture(autouse=True)
def setup_secrets():
    # Setup test token and clear after
    secret_store.set_mock_secret("GITHUB_test-tenant_TOKEN", "mock-token-123")
    yield
    secret_store.clear_mock_secrets()


@pytest.mark.asyncio
async def test_connector_properties(connector: GitHubConnector):
    assert connector.provider == "github"
    assert Capability.GITHUB_REPOSITORY_READ in connector.supported_capabilities


@pytest.mark.asyncio
async def test_health_check_success(connector: GitHubConnector, connection: Connection):
    with patch("httpx.AsyncClient.request", new_callable=AsyncMock) as mock_request:
        mock_response = MagicMock()
        mock_response.is_success = True
        mock_response.status_code = 200
        mock_request.return_value = mock_response

        health = await connector.check_health(connection)

        assert health.status == ConnectionStatus.AVAILABLE
        assert health.provider == "github"


@pytest.mark.asyncio
async def test_health_check_missing_token(connector: GitHubConnector, connection: Connection):
    secret_store.clear_mock_secrets()

    health = await connector.check_health(connection)

    assert health.status == ConnectionStatus.AUTHENTICATION_REQUIRED
    assert health.message == "Missing credentials"


@pytest.mark.asyncio
async def test_health_check_invalid_token(connector: GitHubConnector, connection: Connection):
    with patch("httpx.AsyncClient.request", new_callable=AsyncMock) as mock_request:
        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_request.return_value = mock_response

        health = await connector.check_health(connection)

        assert health.status == ConnectionStatus.AUTHENTICATION_REQUIRED
        assert "credentials" in health.message


@pytest.mark.asyncio
async def test_read_repository_success(connector: GitHubConnector, connection: Connection):
    with patch("httpx.AsyncClient.request", new_callable=AsyncMock) as mock_request:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.is_success = True
        mock_response.json.return_value = {
            "id": 12345,
            "html_url": "https://github.com/owner/repo",
            "visibility": "public",
            "default_branch": "main"
        }
        mock_request.return_value = mock_response

        result = await connector.read_repository(connection, "owner", "repo")

        assert result["resource_type"] == "repository"
        assert result["resource_id"] == "12345"
        assert result["url"] == "https://github.com/owner/repo"


@pytest.mark.asyncio
async def test_read_repository_not_found(connector: GitHubConnector, connection: Connection):
    with patch("httpx.AsyncClient.request", new_callable=AsyncMock) as mock_request:
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_request.return_value = mock_response

        with pytest.raises(NotFoundError, match="not found"):
            await connector.read_repository(connection, "owner", "repo")


@pytest.mark.asyncio
async def test_error_normalization(connector: GitHubConnector, connection: Connection):
    with patch("httpx.AsyncClient.request", new_callable=AsyncMock) as mock_request:
        # Rate limit
        mock_response = MagicMock()
        mock_response.status_code = 403
        mock_response.text = "API rate limit exceeded"
        mock_request.return_value = mock_response
        with pytest.raises(GitHubError, match="rate limit"):
            await connector.read_repository(connection, "owner", "repo")

        # Validation error
        mock_response.status_code = 422
        mock_response.text = "Validation failed"
        mock_request.return_value = mock_response
        with pytest.raises(ValidationError, match="validation error"):
            await connector.read_repository(connection, "owner", "repo")


@pytest.mark.asyncio
async def test_create_issue_success(connector: GitHubConnector, connection: Connection):
    with patch("httpx.AsyncClient.request", new_callable=AsyncMock) as mock_request:
        mock_response = MagicMock()
        mock_response.status_code = 201
        mock_response.is_success = True
        mock_response.json.return_value = {
            "id": 54321,
            "number": 42,
            "title": "Bug fix",
            "html_url": "https://github.com/owner/repo/issues/42"
        }
        mock_request.return_value = mock_response

        result = await connector.create_issue(connection, "owner", "repo", "Bug fix", "Description")

        assert result["resource_type"] == "issue"
        assert result["issue_number"] == 42
        assert result["title"] == "Bug fix"

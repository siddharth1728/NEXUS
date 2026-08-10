import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from app.services import github_service
import httpx
import time

@pytest.mark.asyncio
@patch("app.services.github_service.httpx.AsyncClient")
async def test_get_user_repositories(mock_client_cls):
    mock_client = AsyncMock()
    mock_client_cls.return_value.__aenter__.return_value = mock_client
    
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = [{"id": 123, "name": "repo1", "full_name": "testuser/repo1", "html_url": "http"}]
    mock_client.request = AsyncMock(return_value=mock_resp)
    
    result = await github_service.get_user_repositories("testuser")
    assert len(result) == 1
    assert result[0]["id"] == 123

@pytest.mark.asyncio
@patch("app.services.github_service.httpx.AsyncClient")
async def test_github_rate_limit(mock_client_cls):
    mock_client = AsyncMock()
    mock_client_cls.return_value.__aenter__.return_value = mock_client
    
    mock_resp = MagicMock()
    mock_resp.status_code = 403
    mock_resp.headers = {"X-RateLimit-Reset": str(int(time.time()) + 3600)}
    mock_client.request = AsyncMock(return_value=mock_resp)
    
    with pytest.raises(github_service.GitHubRateLimitException) as exc:
        await github_service.get_user_repositories("testuser")
        
    assert "GitHub sync is temporarily unavailable" in str(exc.value)

@pytest.mark.asyncio
@patch("app.services.github_service.httpx.AsyncClient")
async def test_network_timeout_retry(mock_client_cls):
    mock_client = AsyncMock()
    mock_client_cls.return_value.__aenter__.return_value = mock_client
    
    mock_client.request = AsyncMock(side_effect=httpx.TimeoutException("Timeout"))
    
    with pytest.raises(httpx.TimeoutException):
        await github_service.get_user_repositories("testuser")
        
    assert mock_client.request.call_count == 3

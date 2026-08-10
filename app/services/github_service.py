import httpx
import time
import asyncio
from datetime import datetime, timezone
from fastapi import HTTPException
from app.core.config import settings

class GitHubRateLimitException(Exception):
    def __init__(self, reset_timestamp: int):
        self.reset_timestamp = reset_timestamp
        reset_time = datetime.fromtimestamp(reset_timestamp, timezone.utc)
        time_str = reset_time.strftime("%H:%M")
        self.message = f"GitHub sync is temporarily unavailable. Try again after {time_str}."
        super().__init__(self.message)

def _get_headers():
    headers = {"Accept": "application/vnd.github.v3+json"}
    if settings.GITHUB_TOKEN:
        headers["Authorization"] = f"token {settings.GITHUB_TOKEN}"
    return headers

def _handle_response(response: httpx.Response):
    if response.status_code in (403, 429):
        # Check rate limit
        reset_header = response.headers.get("X-RateLimit-Reset")
        if reset_header:
            raise GitHubRateLimitException(int(reset_header))
        else:
            # Fallback if header missing
            raise GitHubRateLimitException(int(time.time()) + 3600)
    response.raise_for_status()
    return response.json()

async def _request_with_backoff(method: str, url: str, **kwargs):
    max_retries = 3
    base_delay = 1.0
    for attempt in range(max_retries):
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.request(method, url, headers=_get_headers(), **kwargs)
                return _handle_response(response)
        except GitHubRateLimitException:
            raise  # Do NOT retry on rate limits
        except httpx.HTTPStatusError as e:
            if e.response.status_code in (401, 403, 404):
                raise  # Do not retry client errors that are definitive
            # Other HTTP errors might be temporary (e.g. 500), so retry
            if attempt == max_retries - 1:
                raise
        except (httpx.RequestError, httpx.TimeoutException):
            if attempt == max_retries - 1:
                raise
        await asyncio.sleep(base_delay * (2 ** attempt))

async def get_user_repositories(username: str):
    url = f"https://api.github.com/users/{username}/repos?type=public&per_page=100"
    return await _request_with_backoff("GET", url)

async def get_repository_metadata(owner: str, repo_name: str):
    url = f"https://api.github.com/repos/{owner}/{repo_name}"
    return await _request_with_backoff("GET", url)

async def get_repository_branch_head(owner: str, repo_name: str, branch: str):
    url = f"https://api.github.com/repos/{owner}/{repo_name}/commits/{branch}"
    data = await _request_with_backoff("GET", url)
    return data["sha"]

async def get_repository_tree(owner: str, repo_name: str, sha: str):
    url = f"https://api.github.com/repos/{owner}/{repo_name}/git/trees/{sha}?recursive=1"
    return await _request_with_backoff("GET", url)

async def get_file_content(owner: str, repo_name: str, sha: str, file_path: str):
    url = f"https://raw.githubusercontent.com/{owner}/{repo_name}/{sha}/{file_path}"
    max_retries = 3
    base_delay = 1.0
    for attempt in range(max_retries):
        try:
            # We don't use the standard API headers for raw.githubusercontent.com
            # unless it's a private repo, but public works without token.
            # However, if we have a token, we might need it for private repos (out of scope for Phase 2).
            # We will just pass the token if available.
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(url, headers=_get_headers())
                # Handle raw rate limit similarly just in case
                if response.status_code in (403, 429):
                    reset = response.headers.get("X-RateLimit-Reset", int(time.time()) + 3600)
                    raise GitHubRateLimitException(int(reset))
                response.raise_for_status()
                return response.text
        except GitHubRateLimitException:
            raise
        except httpx.HTTPStatusError as e:
            if e.response.status_code in (401, 403, 404):
                raise
            if attempt == max_retries - 1:
                raise
        except (httpx.RequestError, httpx.TimeoutException):
            if attempt == max_retries - 1:
                raise
        await asyncio.sleep(base_delay * (2 ** attempt))
    return None

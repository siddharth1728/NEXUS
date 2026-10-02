"""GitHub Connector — all GitHub API communication lives here."""

from datetime import UTC, datetime
from typing import Any

import httpx

from app.core.errors import ForbiddenError, NotFoundError, UnauthorizedError, ValidationError
from app.core.execution.connectors.base import BaseConnector
from app.core.secrets import secret_store
from app.models.enums import Capability
from app.schemas.connection import Connection, ConnectionStatus, ConnectorHealth


class GitHubError(Exception):
    """Normalized GitHub connector error for non-typed failures."""


class GitHubConnector(BaseConnector):
    """GitHub external integration connector."""

    @property
    def provider(self) -> str:
        return "github"

    @property
    def supported_capabilities(self) -> list[Capability]:
        return [
            Capability.GITHUB_REPOSITORY_READ,
            Capability.GITHUB_ISSUE_READ,
            Capability.GITHUB_ISSUE_CREATE,
            Capability.GITHUB_ISSUE_COMMENT_CREATE,
        ]

    def _get_headers(self, connection: Connection) -> dict[str, str]:
        token = secret_store.get_secret(self.get_credential_key(connection))
        if not token:
            raise UnauthorizedError("GitHub token not configured for connection.")
        return {
            "Accept": "application/vnd.github.v3+json",
            "Authorization": f"Bearer {token}",
            "X-GitHub-Api-Version": "2022-11-28",
        }

    def _normalize_error(self, response: httpx.Response) -> None:
        """Normalize GitHub HTTP errors to NEXUS errors."""
        if response.status_code == 401:
            raise UnauthorizedError("GitHub authentication failed.")
        if response.status_code == 403:
            if "rate limit" in response.text.lower():
                raise GitHubError("GitHub API rate limit exceeded.")
            raise ForbiddenError("GitHub authorization denied.")
        if response.status_code == 404:
            raise NotFoundError(resource_type="GitHub Resource", message="GitHub resource not found.")
        if response.status_code == 422:
            raise ValidationError(f"GitHub validation error: {response.text}")
        if response.status_code >= 500:
            raise GitHubError("GitHub upstream failure.")
        if not response.is_success:
            raise GitHubError(f"GitHub API error: {response.status_code}")

    async def _make_request(
        self,
        method: str,
        url: str,
        connection: Connection,
        json_data: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Centralized HTTP client execution with bounds."""
        headers = self._get_headers(connection)
        timeout = httpx.Timeout(10.0, connect=5.0)

        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.request(method, url, headers=headers, json=json_data)
                self._normalize_error(response)
                if response.status_code == 204:
                    return {}
                result: dict[str, Any] = response.json()
                return result
        except httpx.RequestError as e:
            raise GitHubError(f"GitHub connection failure: {e}") from e

    async def check_health(self, connection: Connection) -> ConnectorHealth:
        """Check if the connection has valid credentials and can reach GitHub."""
        try:
            token = secret_store.get_secret(self.get_credential_key(connection))
            if not token:
                return ConnectorHealth(
                    status=ConnectionStatus.AUTHENTICATION_REQUIRED,
                    provider=self.provider,
                    message="Missing credentials",
                    last_checked=datetime.now(UTC),
                )

            await self._make_request("GET", "https://api.github.com/user", connection)
            return ConnectorHealth(
                status=ConnectionStatus.AVAILABLE,
                provider=self.provider,
                last_checked=datetime.now(UTC),
            )
        except UnauthorizedError:
            return ConnectorHealth(
                status=ConnectionStatus.AUTHENTICATION_REQUIRED,
                provider=self.provider,
                message="Invalid or expired credentials",
                last_checked=datetime.now(UTC),
            )
        except Exception as e:
            return ConnectorHealth(
                status=ConnectionStatus.UNAVAILABLE,
                provider=self.provider,
                message=str(e),
                last_checked=datetime.now(UTC),
            )

    async def read_repository(self, connection: Connection, owner: str, repo: str) -> dict[str, Any]:
        """Read a repository's normalized info."""
        url = f"https://api.github.com/repos/{owner}/{repo}"
        data = await self._make_request("GET", url, connection)
        return {
            "resource_type": "repository",
            "resource_id": str(data["id"]),
            "owner": owner,
            "repository": repo,
            "url": data["html_url"],
            "visibility": data.get("visibility", "unknown"),
            "default_branch": data.get("default_branch", "main"),
        }

    async def read_issue(self, connection: Connection, owner: str, repo: str, issue_number: int) -> dict[str, Any]:
        """Read an issue's normalized info."""
        url = f"https://api.github.com/repos/{owner}/{repo}/issues/{issue_number}"
        data = await self._make_request("GET", url, connection)

        if "pull_request" in data:
            raise ValidationError("Target is a pull request, not an issue.")

        return {
            "resource_type": "issue",
            "resource_id": str(data["id"]),
            "owner": owner,
            "repository": repo,
            "issue_number": data["number"],
            "title": data["title"],
            "state": data["state"],
            "url": data["html_url"],
            "author": data["user"]["login"] if "user" in data and data["user"] else "unknown",
        }

    async def create_issue(
        self, connection: Connection, owner: str, repo: str, title: str, body: str
    ) -> dict[str, Any]:
        """Create a new issue."""
        url = f"https://api.github.com/repos/{owner}/{repo}/issues"
        payload = {"title": title, "body": body}
        data = await self._make_request("POST", url, connection, json_data=payload)
        return {
            "resource_type": "issue",
            "resource_id": str(data["id"]),
            "owner": owner,
            "repository": repo,
            "issue_number": data["number"],
            "title": data["title"],
            "url": data["html_url"],
        }

    async def create_issue_comment(
        self, connection: Connection, owner: str, repo: str, issue_number: int, body: str
    ) -> dict[str, Any]:
        """Create a new comment on an issue."""
        url = f"https://api.github.com/repos/{owner}/{repo}/issues/{issue_number}/comments"
        payload = {"body": body}
        data = await self._make_request("POST", url, connection, json_data=payload)
        return {
            "resource_type": "issue_comment",
            "resource_id": str(data["id"]),
            "owner": owner,
            "repository": repo,
            "issue_number": issue_number,
            "url": data["html_url"],
        }

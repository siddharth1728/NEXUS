"""GitHub Tools — capability-specific wrappers over GitHubConnector."""

from datetime import datetime, timezone
from typing import Any, Dict

from pydantic import BaseModel, Field

from app.core.execution.tool import BaseTool, ExecutionContext
from app.core.execution.connectors.github import GitHubConnector
from app.models.enums import Capability
from app.schemas.connection import Connection, ConnectionStatus


# ─── Strict Input Schemas ────────────────────────────────────────────────────

class GitHubRepositoryInput(BaseModel):
    owner: str = Field(description="The repository owner")
    repository: str = Field(description="The repository name")


class GitHubIssueReadInput(GitHubRepositoryInput):
    issue_number: int = Field(description="The issue number")


class GitHubIssueCreateInput(GitHubRepositoryInput):
    title: str = Field(description="The title of the issue")
    body: str = Field(description="The body content of the issue")


class GitHubCommentCreateInput(GitHubIssueReadInput):
    body: str = Field(description="The body content of the comment")


# ─── Base GitHub Tool ─────────────────────────────────────────────────────────

class BaseGitHubTool(BaseTool):
    """Base class for all GitHub tools.

    Connectors own external API communication.
    Tools own parameter validation and NEXUS wiring.
    """

    def __init__(self, connector: GitHubConnector) -> None:
        self.connector = connector

    def _build_connection(self, context: ExecutionContext) -> Connection:
        """Synthesize a Connection from the authenticated ExecutionContext.

        In production, this would query the ConnectionService.
        For Phase 02C, the secret store is keyed as GITHUB_{tenant_id}_TOKEN.
        """
        now = datetime.now(timezone.utc)
        return Connection(
            id="runtime-connection",
            tenant_id=context.tenant_id,
            user_id=context.user_id,
            provider=self.connector.provider,
            status=ConnectionStatus.AVAILABLE,
            created_at=now,
            updated_at=now,
        )

    async def _execute_impl(self, connection: Connection, parameters: BaseModel) -> Dict[str, Any]:
        raise NotImplementedError

    async def _dry_run_impl(self, parameters: BaseModel) -> Dict[str, Any]:
        """Show what would happen without calling GitHub."""
        return {
            "status": "dry_run",
            "provider": self.connector.provider,
            "capability": self.capability,
            "target": parameters.model_dump(),
            "approval_required": self.capability in (
                Capability.GITHUB_ISSUE_CREATE,
                Capability.GITHUB_ISSUE_COMMENT_CREATE,
            ),
            "message": "Dry run succeeded. No external request made.",
        }

    async def execute(self, parameters: BaseModel, context: ExecutionContext) -> Dict[str, Any]:
        connection = self._build_connection(context)
        if context.dry_run:
            return await self._dry_run_impl(parameters)
        return await self._execute_impl(connection, parameters)


# ─── Concrete GitHub Tools ────────────────────────────────────────────────────

class GitHubRepositoryReadTool(BaseGitHubTool):
    """Read basic repository information."""

    @property
    def tool_id(self) -> str:
        return "github_repository_read_v1"

    @property
    def capability(self) -> Capability:
        return Capability.GITHUB_REPOSITORY_READ

    def get_input_schema(self) -> type[BaseModel]:
        return GitHubRepositoryInput

    async def _execute_impl(self, connection: Connection, parameters: BaseModel) -> Dict[str, Any]:
        if not isinstance(parameters, GitHubRepositoryInput):
            raise TypeError("Invalid parameters type.")
        return await self.connector.read_repository(connection, parameters.owner, parameters.repository)


class GitHubIssueReadTool(BaseGitHubTool):
    """Read a specific issue."""

    @property
    def tool_id(self) -> str:
        return "github_issue_read_v1"

    @property
    def capability(self) -> Capability:
        return Capability.GITHUB_ISSUE_READ

    def get_input_schema(self) -> type[BaseModel]:
        return GitHubIssueReadInput

    async def _execute_impl(self, connection: Connection, parameters: BaseModel) -> Dict[str, Any]:
        if not isinstance(parameters, GitHubIssueReadInput):
            raise TypeError("Invalid parameters type.")
        return await self.connector.read_issue(
            connection, parameters.owner, parameters.repository, parameters.issue_number
        )


class GitHubIssueCreateTool(BaseGitHubTool):
    """Create a new issue — mutation, requires approval by policy."""

    @property
    def tool_id(self) -> str:
        return "github_issue_create_v1"

    @property
    def capability(self) -> Capability:
        return Capability.GITHUB_ISSUE_CREATE

    def get_input_schema(self) -> type[BaseModel]:
        return GitHubIssueCreateInput

    async def _execute_impl(self, connection: Connection, parameters: BaseModel) -> Dict[str, Any]:
        if not isinstance(parameters, GitHubIssueCreateInput):
            raise TypeError("Invalid parameters type.")
        return await self.connector.create_issue(
            connection, parameters.owner, parameters.repository, parameters.title, parameters.body
        )


class GitHubCommentCreateTool(BaseGitHubTool):
    """Create a comment on an issue — mutation, requires approval by policy."""

    @property
    def tool_id(self) -> str:
        return "github_comment_create_v1"

    @property
    def capability(self) -> Capability:
        return Capability.GITHUB_ISSUE_COMMENT_CREATE

    def get_input_schema(self) -> type[BaseModel]:
        return GitHubCommentCreateInput

    async def _execute_impl(self, connection: Connection, parameters: BaseModel) -> Dict[str, Any]:
        if not isinstance(parameters, GitHubCommentCreateInput):
            raise TypeError("Invalid parameters type.")
        return await self.connector.create_issue_comment(
            connection, parameters.owner, parameters.repository, parameters.issue_number, parameters.body
        )

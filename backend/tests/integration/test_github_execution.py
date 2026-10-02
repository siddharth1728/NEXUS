"""Integration tests for the GitHub Tools running through the full execution control plane."""

import uuid
from collections.abc import AsyncGenerator
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.execution.agent_registry import AgentRegistry
from app.core.execution.connectors.github import GitHubConnector
from app.core.execution.policy import PolicyEngine
from app.core.execution.tool_registry import ToolRegistry
from app.core.execution.tools.github_tools import (
    GitHubIssueCreateTool,
    GitHubIssueReadTool,
    GitHubRepositoryReadTool,
)
from app.core.secrets import secret_store
from app.models import Base
from app.models.action import Action
from app.models.enums import ActionStatus, ApprovalDecision, Capability, ExecutionState
from app.schemas.agent import Agent
from app.schemas.execution import ExecutionApproval, ExecutionRequestCreate
from app.services.execution_service import ExecutionService

# ─── Test fixtures ─────────────────────────────────────────────────────────────

TEST_TENANT_ID = uuid.UUID("00000000-0000-4000-8000-000000000001")
TEST_USER_ID = uuid.UUID("00000000-0000-4000-8000-000000000002")


@pytest.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    factory = async_sessionmaker(engine, expire_on_commit=False)
    async with factory() as session:
        yield session
    await engine.dispose()


@pytest.fixture
def github_connector() -> GitHubConnector:
    return GitHubConnector()


@pytest.fixture
def tool_registry(github_connector: GitHubConnector) -> ToolRegistry:
    registry = ToolRegistry()
    registry.register(GitHubRepositoryReadTool(github_connector))
    registry.register(GitHubIssueReadTool(github_connector))
    registry.register(GitHubIssueCreateTool(github_connector))
    return registry


@pytest.fixture
def agent_registry() -> AgentRegistry:
    registry = AgentRegistry()
    registry.register(Agent(
        id="github-agent",
        name="GitHub Agent",
        description="Agent with GitHub capabilities",
        capabilities=[
            Capability.GITHUB_REPOSITORY_READ,
            Capability.GITHUB_ISSUE_READ,
            Capability.GITHUB_ISSUE_CREATE,
            Capability.GITHUB_ISSUE_COMMENT_CREATE,
        ],
    ))
    return registry


@pytest.fixture
def execution_service(db_session: AsyncSession, tool_registry: ToolRegistry, agent_registry: AgentRegistry) -> ExecutionService:
    return ExecutionService(
        session=db_session,
        agent_registry=agent_registry,
        tool_registry=tool_registry,
        policy_engine=PolicyEngine(),
    )


@pytest.fixture
async def test_action(db_session: AsyncSession) -> Action:
    action = Action(
        tenant_id=TEST_TENANT_ID,
        title="Fix deployment bug",
        description="Track the deployment bug in GitHub",
        status=ActionStatus.READY,
    )
    db_session.add(action)
    await db_session.commit()
    await db_session.refresh(action)
    return action


@pytest.fixture(autouse=True)
def setup_secrets() -> Any:
    secret_store.set_mock_secret(f"GITHUB_{TEST_TENANT_ID}_TOKEN", "test-github-token")
    yield
    secret_store.clear_mock_secrets()


# ─── Tests ─────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_read_capability_is_auto_authorized(
    execution_service: ExecutionService, test_action: Action
) -> None:
    """GITHUB_REPOSITORY_READ should be ALLOW → immediately AUTHORIZED."""
    req = ExecutionRequestCreate(
        action_id=test_action.id,
        agent_id="github-agent",
        capability=Capability.GITHUB_REPOSITORY_READ,
        tool_id="github_repository_read_v1",
        parameters={"owner": "acme", "repository": "my-repo"},
    )
    resp = await execution_service.create_request(str(TEST_TENANT_ID), str(TEST_USER_ID), req)
    assert resp.state == ExecutionState.AUTHORIZED


@pytest.mark.asyncio
async def test_create_issue_requires_approval(
    execution_service: ExecutionService, test_action: Action
) -> None:
    """GITHUB_ISSUE_CREATE is a mutation → policy must return REQUIRE_APPROVAL."""
    req = ExecutionRequestCreate(
        action_id=test_action.id,
        agent_id="github-agent",
        capability=Capability.GITHUB_ISSUE_CREATE,
        tool_id="github_issue_create_v1",
        parameters={"owner": "acme", "repository": "my-repo", "title": "Bug", "body": "Details"},
    )
    resp = await execution_service.create_request(str(TEST_TENANT_ID), str(TEST_USER_ID), req)
    assert resp.state == ExecutionState.AWAITING_APPROVAL


@pytest.mark.asyncio
async def test_create_issue_approval_then_execute(
    execution_service: ExecutionService, test_action: Action
) -> None:
    """Full approval → execute path. GitHub API is mocked at the HTTP layer."""
    req = ExecutionRequestCreate(
        action_id=test_action.id,
        agent_id="github-agent",
        capability=Capability.GITHUB_ISSUE_CREATE,
        tool_id="github_issue_create_v1",
        parameters={"owner": "acme", "repository": "my-repo", "title": "Bug", "body": "Details"},
    )

    pending = await execution_service.create_request(str(TEST_TENANT_ID), str(TEST_USER_ID), req)
    assert pending.state == ExecutionState.AWAITING_APPROVAL

    approved = await execution_service.review_execution(
        str(TEST_TENANT_ID),
        str(TEST_USER_ID),
        str(pending.id),
        ExecutionApproval(decision=ApprovalDecision.APPROVED, reason="Looks good"),
    )
    assert approved.state == ExecutionState.AUTHORIZED

    with patch("httpx.AsyncClient.request", new_callable=AsyncMock) as mock_request:
        mock_response = MagicMock()
        mock_response.status_code = 201
        mock_response.is_success = True
        mock_response.json.return_value = {
            "id": 9876,
            "number": 7,
            "title": "Bug",
            "html_url": "https://github.com/acme/my-repo/issues/7",
        }
        mock_request.return_value = mock_response

        result = await execution_service.execute(str(TEST_TENANT_ID), str(approved.id))

    assert result.state == ExecutionState.SUCCEEDED
    assert result.result_payload is not None
    assert result.result_payload["resource_type"] == "issue"
    assert result.result_payload["issue_number"] == 7


@pytest.mark.asyncio
async def test_create_issue_rejected_cannot_execute(
    execution_service: ExecutionService, test_action: Action
) -> None:
    """Rejected execution cannot proceed to execution."""
    req = ExecutionRequestCreate(
        action_id=test_action.id,
        agent_id="github-agent",
        capability=Capability.GITHUB_ISSUE_CREATE,
        tool_id="github_issue_create_v1",
        parameters={"owner": "acme", "repository": "my-repo", "title": "Bug", "body": "Details"},
    )

    pending = await execution_service.create_request(str(TEST_TENANT_ID), str(TEST_USER_ID), req)
    await execution_service.review_execution(
        str(TEST_TENANT_ID),
        str(TEST_USER_ID),
        str(pending.id),
        ExecutionApproval(decision=ApprovalDecision.REJECTED, reason="Not now"),
    )

    with pytest.raises(ValueError, match="Cannot execute"):
        await execution_service.execute(str(TEST_TENANT_ID), str(pending.id))


@pytest.mark.asyncio
async def test_dry_run_shows_approval_requirement(
    execution_service: ExecutionService, test_action: Action
) -> None:
    """Dry run on a mutation capability must show REQUIRE_APPROVAL without calling GitHub."""
    req = ExecutionRequestCreate(
        action_id=test_action.id,
        agent_id="github-agent",
        capability=Capability.GITHUB_ISSUE_CREATE,
        tool_id="github_issue_create_v1",
        parameters={"owner": "acme", "repository": "my-repo", "title": "Bug", "body": "Details"},
    )

    result = await execution_service.dry_run(str(TEST_TENANT_ID), req)
    assert result.policy_decision.value == "REQUIRE_APPROVAL"
    assert result.would_execute is True  # Could proceed (with approval)


@pytest.mark.asyncio
async def test_token_not_leaked_in_result(
    execution_service: ExecutionService, test_action: Action
) -> None:
    """The GitHub token must not appear in the execution result payload."""
    req = ExecutionRequestCreate(
        action_id=test_action.id,
        agent_id="github-agent",
        capability=Capability.GITHUB_REPOSITORY_READ,
        tool_id="github_repository_read_v1",
        parameters={"owner": "acme", "repository": "my-repo"},
    )
    pending = await execution_service.create_request(str(TEST_TENANT_ID), str(TEST_USER_ID), req)

    with patch("httpx.AsyncClient.request", new_callable=AsyncMock) as mock_request:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.is_success = True
        mock_response.json.return_value = {
            "id": 111,
            "html_url": "https://github.com/acme/my-repo",
            "visibility": "private",
            "default_branch": "main",
        }
        mock_request.return_value = mock_response
        result = await execution_service.execute(str(TEST_TENANT_ID), str(pending.id))

    assert result.result_payload is not None
    payload_str = str(result.result_payload)
    assert "test-github-token" not in payload_str
    assert "Bearer" not in payload_str


@pytest.mark.asyncio
async def test_cross_tenant_isolation(
    execution_service: ExecutionService, db_session: AsyncSession
) -> None:
    """Tenant A cannot access execution records belonging to Tenant B."""
    tenant_b = uuid.UUID("00000000-0000-4000-8000-000000000099")
    action_b = Action(
        tenant_id=tenant_b,
        title="Tenant B action",
        description="Tenant B owned action",
        status=ActionStatus.READY,
    )
    db_session.add(action_b)
    await db_session.commit()
    await db_session.refresh(action_b)

    req = ExecutionRequestCreate(
        action_id=action_b.id,
        agent_id="github-agent",
        capability=Capability.GITHUB_REPOSITORY_READ,
        tool_id="github_repository_read_v1",
        parameters={"owner": "acme", "repository": "my-repo"},
    )

    # Tenant A attempts to create request for Tenant B's action — must fail
    with pytest.raises(ValueError, match="not found in tenant"):
        await execution_service.create_request(str(TEST_TENANT_ID), str(TEST_USER_ID), req)


@pytest.mark.asyncio
async def test_parameter_injection_rejected(
    execution_service: ExecutionService, test_action: Action
) -> None:
    """Malicious parameters must be caught by Pydantic schema validation."""
    req = ExecutionRequestCreate(
        action_id=test_action.id,
        agent_id="github-agent",
        capability=Capability.GITHUB_REPOSITORY_READ,
        tool_id="github_repository_read_v1",
        # Missing required fields — should raise validation error
        parameters={"malicious_key": "../../../etc/passwd"},
    )

    with pytest.raises(ValueError, match="Parameter validation failed"):
        await execution_service.create_request(str(TEST_TENANT_ID), str(TEST_USER_ID), req)


@pytest.mark.asyncio
async def test_idempotency_prevents_duplicate_issue(
    execution_service: ExecutionService, test_action: Action
) -> None:
    """Creating a duplicate request for same action+tool must be blocked."""
    req = ExecutionRequestCreate(
        action_id=test_action.id,
        agent_id="github-agent",
        capability=Capability.GITHUB_ISSUE_CREATE,
        tool_id="github_issue_create_v1",
        parameters={"owner": "acme", "repository": "my-repo", "title": "Bug", "body": "Details"},
    )

    await execution_service.create_request(str(TEST_TENANT_ID), str(TEST_USER_ID), req)

    with pytest.raises(ValueError, match="Idempotency violation"):
        await execution_service.create_request(str(TEST_TENANT_ID), str(TEST_USER_ID), req)

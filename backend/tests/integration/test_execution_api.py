"""Integration tests for Execution API."""

import uuid
from collections.abc import AsyncGenerator

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db_session
from app.models.action import Action
from app.models.enums import ExecutionState
from app.models.tenant import Tenant

TEST_TENANT_ID = uuid.UUID("00000000-0000-4000-8000-000000000001")


@pytest.fixture
async def active_tenant(in_memory_db_session: AsyncSession) -> Tenant:
    tenant = await in_memory_db_session.get(Tenant, TEST_TENANT_ID)
    if not tenant:
        tenant = Tenant(name="API Test Tenant", id=TEST_TENANT_ID)
        in_memory_db_session.add(tenant)
        await in_memory_db_session.commit()
    return tenant


@pytest.fixture
async def test_action(in_memory_db_session: AsyncSession, active_tenant: Tenant) -> Action:
    action = Action(
        id=uuid.uuid4(),
        tenant_id=active_tenant.id,
        title="Test Action",
        description="To execute",
    )
    in_memory_db_session.add(action)
    await in_memory_db_session.commit()
    return action

@pytest.fixture
async def override_get_db(in_memory_db_session: AsyncSession) -> AsyncGenerator[AsyncSession, None]:
    async def _override():  # type: ignore
        yield in_memory_db_session
    return _override  # type: ignore

@pytest.fixture(autouse=True)
def setup_overrides(test_app, in_memory_db_session: AsyncSession):  # type: ignore
    async def _override():  # type: ignore
        yield in_memory_db_session
    test_app.dependency_overrides[get_db_session] = _override
    yield
    test_app.dependency_overrides.pop(get_db_session, None)


@pytest.mark.asyncio
async def test_dry_run_execution(
    async_client: AsyncClient, test_action: Action
) -> None:
    request_data = {
        "action_id": str(test_action.id),
        "agent_id": "simulator",
        "capability": "SYSTEM_SIMULATE",
        "tool_id": "simulate_v1",
        "parameters": {
            "action_type": "test_dry_run",
            "requires_approval": True
        }
    }

    response = await async_client.post(
        "/api/v1/execution/dry-run",
        json=request_data,
        headers={"X-Tenant-ID": str(TEST_TENANT_ID)},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["would_execute"] is True
    assert data["policy_decision"] == "REQUIRE_APPROVAL"


@pytest.mark.asyncio
async def test_end_to_end_simulated_execution(  # type: ignore
    async_client: AsyncClient, test_action: Action, test_app
) -> None:
    # 1. Action exists.
    # 2. Agent proposes execution. (We submit the execution request)
    # 3. Capability is resolved, Policy evaluated, Approval required.
    request_data = {
        "action_id": str(test_action.id),
        "agent_id": "simulator",
        "capability": "SYSTEM_SIMULATE",
        "tool_id": "simulate_v1",
        "parameters": {
            "action_type": "create_calendar_event",
            "mock_payload": {"event_id": "12345"},
            "requires_approval": True
        }
    }

    resp_create = await async_client.post(
        "/api/v1/execution/",
        json=request_data,
        headers={"X-Tenant-ID": str(TEST_TENANT_ID)},
    )

    assert resp_create.status_code == 201
    data = resp_create.json()
    assert data["state"] == ExecutionState.AWAITING_APPROVAL

    execution_id = data["id"]

    # Verify idempotency (Duplicate request)
    resp_dup = await async_client.post(
        "/api/v1/execution/",
        json=request_data,
        headers={"X-Tenant-ID": str(TEST_TENANT_ID)},
    )
    assert resp_dup.status_code == 400

    # 6. Mock approval granted.
    resp_approve = await async_client.post(
        f"/api/v1/execution/{execution_id}/approve",
        json={"decision": "APPROVED", "reason": "Looks good"},
        headers={"X-Tenant-ID": str(TEST_TENANT_ID)},
    )
    assert resp_approve.status_code == 200
    assert resp_approve.json()["state"] == ExecutionState.AUTHORIZED

    # 7. Mock executor runs.
    resp_exec = await async_client.post(
        f"/api/v1/execution/{execution_id}/execute",
        headers={"X-Tenant-ID": str(TEST_TENANT_ID)},
    )
    assert resp_exec.status_code == 200
    assert resp_exec.json()["state"] == ExecutionState.SUCCEEDED

    # 8. Result persisted.
    resp_get = await async_client.get(
        f"/api/v1/execution/{execution_id}",
        headers={"X-Tenant-ID": str(TEST_TENANT_ID)},
    )
    assert resp_get.status_code == 200
    assert resp_get.json()["result_payload"]["status"] == "success"


@pytest.mark.asyncio
async def test_tenant_isolation(  # type: ignore
    async_client: AsyncClient, test_action: Action, in_memory_db_session: AsyncSession, test_app
) -> None:
    # Attempt to access cross tenant
    other_tenant_id = uuid.uuid4()

    # Temporarily override get_current_tenant_id to return other_tenant_id
    from app.api.deps import get_current_tenant_id
    test_app.dependency_overrides[get_current_tenant_id] = lambda: other_tenant_id

    # Create request using actual tenant
    request_data = {
        "action_id": str(test_action.id),
        "agent_id": "simulator",
        "capability": "SYSTEM_SIMULATE",
        "tool_id": "simulate_v1",
        "parameters": {
            "action_type": "test_tenant",
        }
    }

    # Trying to create request for action_id belonging to TEST_TENANT_ID but as other_tenant_id
    resp = await async_client.post(
        "/api/v1/execution/",
        json=request_data,
        headers={"X-Tenant-ID": str(other_tenant_id)},
    )
    test_app.dependency_overrides.pop(get_current_tenant_id, None)

    assert resp.status_code == 400  # Action not found in tenant


@pytest.mark.asyncio
async def test_unauthorized_capability(
    async_client: AsyncClient, test_action: Action
) -> None:
    # Agent 'simulator' does NOT have capability EMAIL_SEND
    request_data = {
        "action_id": str(test_action.id),
        "agent_id": "simulator",
        "capability": "EMAIL_SEND",
        "tool_id": "simulate_v1", # (Tool also doesn't provide this, but agent capability check fails first)
        "parameters": {}
    }

    resp = await async_client.post(
        "/api/v1/execution/",
        json=request_data,
        headers={"X-Tenant-ID": str(TEST_TENANT_ID)},
    )
    assert resp.status_code == 400
    assert "lacks capability" in resp.json()["error"]["message"]


@pytest.mark.asyncio
async def test_malformed_parameters(
    async_client: AsyncClient, test_action: Action
) -> None:
    request_data = {
        "action_id": str(test_action.id),
        "agent_id": "simulator",
        "capability": "SYSTEM_SIMULATE",
        "tool_id": "simulate_v1",
        "parameters": {
            # Missing "action_type", a required field in SimulatedToolInput
            "should_fail": True
        }
    }

    resp = await async_client.post(
        "/api/v1/execution/",
        json=request_data,
        headers={"X-Tenant-ID": str(TEST_TENANT_ID)},
    )
    assert resp.status_code == 400
    assert "Parameter validation failed" in resp.json()["error"]["message"]

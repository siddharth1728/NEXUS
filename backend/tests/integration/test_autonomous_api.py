"""Integration tests for Autonomous Loop API endpoint."""

import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db_session
from app.models.action import Action
from app.models.enums import ActionStatus, AutonomyMode
from app.models.tenant import Tenant

TEST_TENANT_ID = uuid.UUID("00000000-0000-4000-8000-000000000001")


@pytest.fixture
async def active_tenant(in_memory_db_session: AsyncSession) -> Tenant:
    tenant = await in_memory_db_session.get(Tenant, TEST_TENANT_ID)
    if not tenant:
        tenant = Tenant(name="Autonomous Test Tenant", id=TEST_TENANT_ID)
        in_memory_db_session.add(tenant)
        await in_memory_db_session.commit()
    return tenant


@pytest.fixture
async def ready_action(in_memory_db_session: AsyncSession, active_tenant: Tenant) -> Action:
    action = Action(
        id=uuid.uuid4(),
        tenant_id=active_tenant.id,
        title="Simulated action for autonomous run",
        description="Safe test action",
        status=ActionStatus.READY,
    )
    in_memory_db_session.add(action)
    await in_memory_db_session.commit()
    return action


@pytest.fixture(autouse=True)
def setup_overrides(test_app, in_memory_db_session: AsyncSession):  # type: ignore
    async def _override():  # type: ignore
        yield in_memory_db_session
    test_app.dependency_overrides[get_db_session] = _override
    yield
    test_app.dependency_overrides.pop(get_db_session, None)


@pytest.mark.asyncio
async def test_autonomous_endpoint_run(
    async_client: AsyncClient, ready_action: Action
) -> None:
    response = await async_client.post(
        "/api/v1/autonomous/run",
        params={"mode": AutonomyMode.AUTONOMOUS_WITHIN_POLICY, "max_iterations": 2},
    )
    assert response.status_code == 200
    data = response.json()
    assert "iterations_run" in data
    assert "stop_reason" in data
    assert "actions_taken" in data

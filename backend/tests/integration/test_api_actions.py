"""Integration tests for Actions API endpoints."""

import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enums import ActionStatus, EdgeRelationType
from app.models.tenant import Tenant


@pytest.fixture
async def active_tenant(in_memory_db_session: AsyncSession) -> Tenant:
    tenant = Tenant(name="API Test Tenant", id=uuid.UUID("00000000-0000-4000-8000-000000000001"))
    in_memory_db_session.add(tenant)
    await in_memory_db_session.commit()
    return tenant


@pytest.fixture
async def other_tenant(in_memory_db_session: AsyncSession) -> Tenant:
    tenant = Tenant(name="Other Tenant", id=uuid.uuid4())
    in_memory_db_session.add(tenant)
    await in_memory_db_session.commit()
    return tenant


@pytest.mark.asyncio
@pytest.mark.integration
async def test_create_action(async_client: AsyncClient, active_tenant: Tenant) -> None:
    payload = {"title": "Test Action", "description": "Needs doing", "priority": "P1"}
    response = await async_client.post("/api/v1/actions", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == payload["title"]
    assert data["status"] == ActionStatus.CANDIDATE
    assert data["tenant_id"] == str(active_tenant.id)


@pytest.mark.asyncio
@pytest.mark.integration
async def test_action_state_transitions(async_client: AsyncClient, active_tenant: Tenant) -> None:
    # Create action
    create_payload = {"title": "Transition Test", "description": "TBD"}
    create_resp = await async_client.post("/api/v1/actions", json=create_payload)
    action_id = create_resp.json()["id"]

    # Valid transition (CANDIDATE -> READY)
    resp1 = await async_client.post(
        f"/api/v1/actions/{action_id}/transition", json={"new_status": ActionStatus.READY}
    )
    assert resp1.status_code == 200
    assert resp1.json()["status"] == ActionStatus.READY

    # Invalid transition (READY -> COMPLETED directly)
    resp2 = await async_client.post(
        f"/api/v1/actions/{action_id}/transition", json={"new_status": ActionStatus.COMPLETED}
    )
    assert resp2.status_code == 409  # Conflict


@pytest.mark.asyncio
@pytest.mark.integration
async def test_action_dependencies_and_cycles(
    async_client: AsyncClient, active_tenant: Tenant
) -> None:
    # Create Action A
    resp_a = await async_client.post(
        "/api/v1/actions", json={"title": "Action A", "description": "A"}
    )
    action_a_id = resp_a.json()["id"]

    # Create Action B
    resp_b = await async_client.post(
        "/api/v1/actions", json={"title": "Action B", "description": "B"}
    )
    action_b_id = resp_b.json()["id"]

    # Create edge A -> depends_on -> B
    resp_edge = await async_client.post(
        f"/api/v1/actions/{action_a_id}/dependencies",
        json={"target_id": action_b_id, "relation_type": EdgeRelationType.DEPENDS_ON},
    )
    assert resp_edge.status_code == 201

    # Attempt cycle B -> depends_on -> A
    resp_cycle = await async_client.post(
        f"/api/v1/actions/{action_b_id}/dependencies",
        json={"target_id": action_a_id, "relation_type": EdgeRelationType.DEPENDS_ON},
    )
    assert resp_cycle.status_code == 400
    assert resp_cycle.json()["error"]["code"] == "DEPENDENCY_CYCLE_DETECTED"

    # Attempt duplicate A -> depends_on -> B
    resp_dup = await async_client.post(
        f"/api/v1/actions/{action_a_id}/dependencies",
        json={"target_id": action_b_id, "relation_type": EdgeRelationType.DEPENDS_ON},
    )
    assert resp_dup.status_code == 409

    # Retrieve dependencies
    resp_get = await async_client.get(f"/api/v1/actions/{action_a_id}/dependencies")
    assert resp_get.status_code == 200
    assert len(resp_get.json()) == 1


@pytest.mark.asyncio
@pytest.mark.integration
async def test_tenant_isolation(
    async_client: AsyncClient,
    active_tenant: Tenant,
    other_tenant: Tenant,
    in_memory_db_session: AsyncSession,
) -> None:
    # Create action in other tenant directly in DB
    from app.models.action import Action

    action = Action(tenant_id=other_tenant.id, title="Other Tenant Action", description="Private")
    in_memory_db_session.add(action)
    await in_memory_db_session.commit()

    # Current tenant (active_tenant mock ID) attempts to access it
    resp = await async_client.get(f"/api/v1/actions/{action.id}")
    assert resp.status_code == 404

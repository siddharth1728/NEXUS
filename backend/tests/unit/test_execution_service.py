"""Unit tests for the Execution Service and components."""

import uuid

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.execution.agent_registry import AgentRegistry
from app.core.execution.policy import PolicyEngine
from app.core.execution.tool_registry import ToolRegistry
from app.core.execution.tools.simulate import SimulatedTool
from app.models.action import Action
from app.models.enums import ApprovalDecision, Capability, ExecutionState, PolicyDecision
from app.schemas.agent import Agent
from app.schemas.execution import ExecutionApproval, ExecutionRequestCreate
from app.services.execution_service import ExecutionService

TEST_TENANT_ID = uuid.UUID("00000000-0000-4000-8000-000000000001")


@pytest.fixture
def agent_registry() -> AgentRegistry:
    registry = AgentRegistry()
    registry.register(Agent(
        id="simulator",
        name="Simulator",
        description="Simulator",
        capabilities=[Capability.SYSTEM_SIMULATE, Capability.DOCUMENT_READ, Capability.EMAIL_SEND]
    ))
    return registry


@pytest.fixture
def tool_registry() -> ToolRegistry:
    registry = ToolRegistry()
    registry.register(SimulatedTool())
    return registry


@pytest.fixture
def policy_engine() -> PolicyEngine:
    return PolicyEngine()


@pytest.fixture
async def execution_service(
    in_memory_db_session: AsyncSession,
    agent_registry: AgentRegistry,
    tool_registry: ToolRegistry,
    policy_engine: PolicyEngine
) -> ExecutionService:
    return ExecutionService(
        session=in_memory_db_session,
        agent_registry=agent_registry,
        tool_registry=tool_registry,
        policy_engine=policy_engine
    )


@pytest.fixture
async def test_action(in_memory_db_session: AsyncSession) -> Action:
    action = Action(
        id=uuid.uuid4(),
        tenant_id=TEST_TENANT_ID,
        title="Test",
        description="Test"
    )
    in_memory_db_session.add(action)
    await in_memory_db_session.commit()
    return action


@pytest.mark.asyncio
async def test_create_request_success(
    execution_service: ExecutionService,
    test_action: Action
) -> None:
    request = ExecutionRequestCreate(
        action_id=test_action.id,
        agent_id="simulator",
        capability=Capability.SYSTEM_SIMULATE,
        tool_id="simulate_v1",
        parameters={"action_type": "test_auth", "requires_approval": False}
    )

    resp = await execution_service.create_request(str(TEST_TENANT_ID), str(uuid.uuid4()), request)
    assert resp.state == ExecutionState.AUTHORIZED
    assert resp.action_id == test_action.id

    # Test Idempotency
    with pytest.raises(ValueError, match="Idempotency violation"):
        await execution_service.create_request(str(TEST_TENANT_ID), str(uuid.uuid4()), request)


@pytest.mark.asyncio
async def test_create_request_failures(
    execution_service: ExecutionService,
    test_action: Action
) -> None:
    # Action not found
    req = ExecutionRequestCreate(
        action_id=uuid.uuid4(), agent_id="simulator", capability=Capability.SYSTEM_SIMULATE, tool_id="simulate_v1", parameters={"action_type": "test"}
    )
    with pytest.raises(ValueError, match="not found in tenant"):
        await execution_service.create_request(str(TEST_TENANT_ID), None, req)

    # Agent not registered
    req.action_id = test_action.id
    req.agent_id = "unknown"
    with pytest.raises(ValueError, match="is not registered"):
        await execution_service.create_request(str(TEST_TENANT_ID), None, req)

    # Tool not registered
    req.agent_id = "simulator"
    req.tool_id = "unknown_tool"
    with pytest.raises(ValueError, match="is not registered"):
        await execution_service.create_request(str(TEST_TENANT_ID), None, req)

    # Capability mismatch in agent
    req.tool_id = "simulate_v1"
    req.capability = Capability.GITHUB_CREATE_ISSUE  # Agent doesn't have this
    with pytest.raises(ValueError, match="lacks capability"):
        await execution_service.create_request(str(TEST_TENANT_ID), None, req)

    # Capability mismatch in tool
    req.capability = Capability.EMAIL_SEND  # Agent has it, but SimulatedTool doesn't provide it
    with pytest.raises(ValueError, match="does not provide capability"):
        await execution_service.create_request(str(TEST_TENANT_ID), None, req)

    # Parameter validation failure
    req.capability = Capability.SYSTEM_SIMULATE
    req.parameters = {}  # Missing action_type
    with pytest.raises(ValueError, match="Parameter validation failed"):
        await execution_service.create_request(str(TEST_TENANT_ID), None, req)


@pytest.mark.asyncio
async def test_review_and_execute(
    execution_service: ExecutionService,
    test_action: Action
) -> None:
    request = ExecutionRequestCreate(
        action_id=test_action.id,
        agent_id="simulator",
        capability=Capability.SYSTEM_SIMULATE,
        tool_id="simulate_v1",
        parameters={"action_type": "test_approval", "requires_approval": True}
    )

    resp = await execution_service.create_request(str(TEST_TENANT_ID), str(uuid.uuid4()), request)
    assert resp.state == ExecutionState.AWAITING_APPROVAL

    # Fetch
    fetched = await execution_service.get_execution(str(TEST_TENANT_ID), str(resp.id))
    assert fetched is not None
    assert fetched.id == resp.id

    # Invalid transition (Execute while AWAITING_APPROVAL)
    with pytest.raises(ValueError, match="Cannot execute record in state"):
        await execution_service.execute(str(TEST_TENANT_ID), str(resp.id))

    # Review Reject
    reject_appr = ExecutionApproval(decision=ApprovalDecision.REJECTED, reason="No")
    resp_rej = await execution_service.review_execution(str(TEST_TENANT_ID), str(uuid.uuid4()), str(resp.id), reject_appr)
    assert resp_rej.state == ExecutionState.REJECTED

    # Review Invalid Transition
    with pytest.raises(ValueError, match="Cannot review execution in state"):
        await execution_service.review_execution(str(TEST_TENANT_ID), str(uuid.uuid4()), str(resp.id), reject_appr)

    # Execute Rejected (should fail)
    with pytest.raises(ValueError, match="Cannot execute record in state"):
        await execution_service.execute(str(TEST_TENANT_ID), str(resp.id))

    # New Request -> Approve -> Execute
    request.parameters["action_type"] = "test_approval_2"
    resp2 = await execution_service.create_request(str(TEST_TENANT_ID), str(uuid.uuid4()), request)

    approve_appr = ExecutionApproval(decision=ApprovalDecision.APPROVED, reason="Yes")
    resp2_appr = await execution_service.review_execution(str(TEST_TENANT_ID), str(uuid.uuid4()), str(resp2.id), approve_appr)
    assert resp2_appr.state == ExecutionState.AUTHORIZED

    # Execute Success
    resp2_exec = await execution_service.execute(str(TEST_TENANT_ID), str(resp2.id))
    assert resp2_exec.state == ExecutionState.SUCCEEDED

    # Invalid execute (already SUCCEEDED)
    with pytest.raises(ValueError, match="Cannot execute record in state"):
        await execution_service.execute(str(TEST_TENANT_ID), str(resp2.id))


@pytest.mark.asyncio
async def test_tool_failure_execution(
    execution_service: ExecutionService,
    test_action: Action
) -> None:
    request = ExecutionRequestCreate(
        action_id=test_action.id,
        agent_id="simulator",
        capability=Capability.SYSTEM_SIMULATE,
        tool_id="simulate_v1",
        parameters={"action_type": "fail_me", "should_fail": True}
    )

    resp = await execution_service.create_request(str(TEST_TENANT_ID), str(uuid.uuid4()), request)
    assert resp.state == ExecutionState.AUTHORIZED

    resp_exec = await execution_service.execute(str(TEST_TENANT_ID), str(resp.id))
    assert resp_exec.state == ExecutionState.FAILED
    assert resp_exec.error_message is not None
    assert "Simulated intentional failure" in resp_exec.error_message


@pytest.mark.asyncio
async def test_execution_not_found(
    execution_service: ExecutionService
) -> None:
    assert await execution_service.get_execution(str(TEST_TENANT_ID), str(uuid.uuid4())) is None

    with pytest.raises(ValueError, match="Execution record not found"):
        await execution_service.review_execution(str(TEST_TENANT_ID), str(uuid.uuid4()), str(uuid.uuid4()), ExecutionApproval(decision=ApprovalDecision.APPROVED))

    with pytest.raises(ValueError, match="Execution record not found"):
        await execution_service.execute(str(TEST_TENANT_ID), str(uuid.uuid4()))


@pytest.mark.asyncio
async def test_tool_deleted_mid_execution(
    execution_service: ExecutionService,
    test_action: Action,
    in_memory_db_session: AsyncSession
) -> None:
    request = ExecutionRequestCreate(
        action_id=test_action.id,
        agent_id="simulator",
        capability=Capability.SYSTEM_SIMULATE,
        tool_id="simulate_v1",
        parameters={"action_type": "deleted_tool"}
    )

    resp = await execution_service.create_request(str(TEST_TENANT_ID), str(uuid.uuid4()), request)

    # Delete tool from registry
    execution_service.tool_registry._tools.clear()

    with pytest.raises(ValueError, match="Tool no longer exists"):
        await execution_service.execute(str(TEST_TENANT_ID), str(resp.id))

    # Check DB state
    fetched = await execution_service.get_execution(str(TEST_TENANT_ID), str(resp.id))
    assert fetched is not None
    assert fetched.state == ExecutionState.FAILED
    assert fetched.error_message == "Tool no longer exists."


@pytest.mark.asyncio
async def test_dry_run_service(
    execution_service: ExecutionService,
    test_action: Action
) -> None:
    request = ExecutionRequestCreate(
        action_id=test_action.id,
        agent_id="simulator",
        capability=Capability.DOCUMENT_READ, # ALLOW
        tool_id="simulate_v1",
        parameters={"action_type": "dry"}
    )

    res = await execution_service.dry_run(str(TEST_TENANT_ID), request)
    assert res.would_execute is True
    assert res.policy_decision == PolicyDecision.ALLOW

    # REQUIRE_APPROVAL
    request.capability = Capability.EMAIL_SEND
    res = await execution_service.dry_run(str(TEST_TENANT_ID), request)
    assert res.would_execute is True
    assert res.policy_decision == PolicyDecision.REQUIRE_APPROVAL
    assert res.reason == "Requires human approval."

    # DENY (using unknown/default for PolicyEngine)
    request.capability = Capability.EMAIL_DRAFT
    res = await execution_service.dry_run(str(TEST_TENANT_ID), request)
    assert res.would_execute is False
    assert res.policy_decision == PolicyDecision.DENY
    assert res.reason == "Capability is denied by policy."

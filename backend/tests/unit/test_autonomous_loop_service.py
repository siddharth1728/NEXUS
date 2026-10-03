"""Unit tests for Autonomous Loop Service."""

import uuid
from datetime import datetime, timezone
import pytest
from unittest.mock import AsyncMock, MagicMock

from app.models.enums import ActionStatus, AutonomyMode, Capability, ConfidenceLevel, ExecutionState, PolicyDecision, RiskTier
from app.schemas.action import ActionResponse
from app.schemas.execution import ExecutionResponse
from app.services.autonomous_loop_service import AutonomousLoopService

@pytest.fixture
def autonomous_loop_service():
    action_service = AsyncMock()
    execution_service = AsyncMock()
    verification_service = AsyncMock()
    workflow_engine = AsyncMock()
    db = AsyncMock()

    service = AutonomousLoopService(
        db=db,
        action_service=action_service,
        execution_service=execution_service,
        verification_service=verification_service,
        workflow_engine=workflow_engine,
    )
    return service, action_service, execution_service, verification_service, workflow_engine

@pytest.mark.asyncio
async def test_run_loop_no_eligible_actions(autonomous_loop_service):
    service, action_service, _, _, _ = autonomous_loop_service
    action_service.list_actions.return_value = ([], 0)
    
    tenant_id = uuid.uuid4()
    result = await service.run_loop(tenant_id, AutonomyMode.AUTONOMOUS_WITHIN_POLICY, 5)
    
    assert result["stop_reason"] == "NO_ELIGIBLE_ACTIONS"
    assert result["iterations_run"] == 1

@pytest.mark.asyncio
async def test_run_loop_policy_denied(autonomous_loop_service):
    service, action_service, _, _, _ = autonomous_loop_service
    
    now = datetime.now(timezone.utc)
    action = ActionResponse(
        id=uuid.uuid4(),
        tenant_id=uuid.uuid4(),
        title="Delete secret data",
        description="Dangerous mutation",
        status=ActionStatus.READY,
        confidence=ConfidenceLevel.HIGH,
        priority="P1",
        source_document_id=uuid.uuid4(),
        created_at=now,
        updated_at=now,
    )
    action_service.list_actions.return_value = ([action], 1)
    
    service._evaluate_policy = MagicMock(return_value=PolicyDecision.DENY)
    
    tenant_id = uuid.uuid4()
    result = await service.run_loop(tenant_id, AutonomyMode.AUTONOMOUS_WITHIN_POLICY, 5)
    
    assert result["stop_reason"] == "POLICY_DENIED"
    assert result["iterations_run"] == 1

@pytest.mark.asyncio
async def test_run_loop_execution_success(autonomous_loop_service):
    service, action_service, execution_service, verification_service, _ = autonomous_loop_service
    
    now = datetime.now(timezone.utc)
    action = ActionResponse(
        id=uuid.uuid4(),
        tenant_id=uuid.uuid4(),
        title="Simulate workflow check",
        description="Verify simulation runs fine",
        status=ActionStatus.READY,
        confidence=ConfidenceLevel.HIGH,
        priority="P2",
        source_document_id=uuid.uuid4(),
        created_at=now,
        updated_at=now,
    )
    
    # Needs to return eligible action first iteration, then empty second iteration
    action_service.list_actions.side_effect = [([action], 1), ([], 0)]
    
    exec_req = ExecutionResponse(
        id=uuid.uuid4(),
        action_id=action.id,
        tenant_id=uuid.uuid4(),
        agent_id="autonomous_loop",
        capability=Capability.SYSTEM_SIMULATE,
        tool_id="simulate_v1",
        parameters={"action_type": action.title},
        state=ExecutionState.SUCCEEDED,
        policy_decision=PolicyDecision.ALLOW,
        created_at=now,
        updated_at=now,
    )
    execution_service.create_request.return_value = exec_req
    execution_service.execute.return_value = exec_req
    
    verification_service.verify_action.return_value = True
    
    tenant_id = uuid.uuid4()
    result = await service.run_loop(tenant_id, AutonomyMode.AUTONOMOUS_WITHIN_POLICY, 5)
    
    assert result["stop_reason"] == "NO_ELIGIBLE_ACTIONS"
    assert result["iterations_run"] == 2
    assert len(result["actions_taken"]) == 1

@pytest.mark.asyncio
async def test_run_loop_execution_failed(autonomous_loop_service):
    service, action_service, execution_service, _, _ = autonomous_loop_service
    now = datetime.now(timezone.utc)
    action = ActionResponse(
        id=uuid.uuid4(),
        tenant_id=uuid.uuid4(),
        title="Simulate task",
        description="Failing action",
        status=ActionStatus.READY,
        confidence=ConfidenceLevel.HIGH,
        priority="P2",
        source_document_id=uuid.uuid4(),
        created_at=now,
        updated_at=now,
    )
    action_service.list_actions.return_value = ([action], 1)
    
    exec_req = ExecutionResponse(
        id=uuid.uuid4(),
        action_id=action.id,
        tenant_id=uuid.uuid4(),
        agent_id="autonomous_loop",
        capability=Capability.SYSTEM_SIMULATE,
        tool_id="simulate_v1",
        parameters={"action_type": action.title},
        state=ExecutionState.FAILED,
        policy_decision=PolicyDecision.ALLOW,
        created_at=now,
        updated_at=now,
    )
    execution_service.create_request.return_value = exec_req
    execution_service.execute.return_value = exec_req
    
    result = await service.run_loop(uuid.uuid4(), AutonomyMode.AUTONOMOUS_WITHIN_POLICY, 3)
    assert result["stop_reason"] == "EXECUTION_FAILED"

@pytest.mark.asyncio
async def test_run_loop_verification_failed(autonomous_loop_service):
    service, action_service, execution_service, verification_service, _ = autonomous_loop_service
    now = datetime.now(timezone.utc)
    action = ActionResponse(
        id=uuid.uuid4(),
        tenant_id=uuid.uuid4(),
        title="Simulate task",
        description="Unverified action",
        status=ActionStatus.READY,
        confidence=ConfidenceLevel.HIGH,
        priority="P2",
        source_document_id=uuid.uuid4(),
        created_at=now,
        updated_at=now,
    )
    action_service.list_actions.return_value = ([action], 1)
    
    exec_req = ExecutionResponse(
        id=uuid.uuid4(),
        action_id=action.id,
        tenant_id=uuid.uuid4(),
        agent_id="autonomous_loop",
        capability=Capability.SYSTEM_SIMULATE,
        tool_id="simulate_v1",
        parameters={"action_type": action.title},
        state=ExecutionState.SUCCEEDED,
        policy_decision=PolicyDecision.ALLOW,
        created_at=now,
        updated_at=now,
    )
    execution_service.create_request.return_value = exec_req
    execution_service.execute.return_value = exec_req
    verification_service.verify_action.return_value = False
    
    result = await service.run_loop(uuid.uuid4(), AutonomyMode.AUTONOMOUS_WITHIN_POLICY, 3)
    assert result["stop_reason"] == "VERIFICATION_FAILED"

@pytest.mark.asyncio
async def test_run_loop_requires_approval_halt(autonomous_loop_service):
    service, action_service, execution_service, _, _ = autonomous_loop_service
    now = datetime.now(timezone.utc)
    action = ActionResponse(
        id=uuid.uuid4(),
        tenant_id=uuid.uuid4(),
        title="Send email alert",
        description="email notification to client",
        status=ActionStatus.READY,
        confidence=ConfidenceLevel.HIGH,
        priority="P1",
        source_document_id=uuid.uuid4(),
        created_at=now,
        updated_at=now,
    )
    action_service.list_actions.return_value = ([action], 1)
    
    exec_req = ExecutionResponse(
        id=uuid.uuid4(),
        action_id=action.id,
        tenant_id=uuid.uuid4(),
        agent_id="autonomous_loop",
        capability=Capability.EMAIL_DRAFT,
        tool_id="email_draft",
        parameters={"action_id": str(action.id), "title": action.title},
        state=ExecutionState.AWAITING_APPROVAL,
        policy_decision=PolicyDecision.REQUIRE_APPROVAL,
        created_at=now,
        updated_at=now,
    )
    execution_service.create_request.return_value = exec_req

    
    result = await service.run_loop(uuid.uuid4(), AutonomyMode.MANUAL, 3)
    assert result["stop_reason"] == "REQUIRES_APPROVAL"
    assert result["actions_taken"][0]["status"] == "AWAITING_APPROVAL"

def test_determine_capability_routing():
    service = AutonomousLoopService(None, None, None, None, None) # type: ignore
    now = datetime.now(timezone.utc)
    gh_action = ActionResponse(
        id=uuid.uuid4(), tenant_id=uuid.uuid4(), title="Create GitHub Issue for bug",
        description="issue on repo", status=ActionStatus.READY, confidence=ConfidenceLevel.HIGH,
        priority="P2", source_document_id=None, created_at=now, updated_at=now
    )
    cal_action = ActionResponse(
        id=uuid.uuid4(), tenant_id=uuid.uuid4(), title="Add to calendar",
        description="meeting invite", status=ActionStatus.READY, confidence=ConfidenceLevel.HIGH,
        priority="P2", source_document_id=None, created_at=now, updated_at=now
    )
    
    assert service._determine_capability(gh_action) == Capability.GITHUB_ISSUE_CREATE
    assert service._get_tool_id_for_capability(Capability.GITHUB_ISSUE_CREATE) == "github_issue_create"
    assert service._determine_capability(cal_action) == Capability.CALENDAR_CREATE
    assert service._get_tool_id_for_capability(Capability.CALENDAR_CREATE) == "calendar_create"

def test_determine_risk_tier():
    service = AutonomousLoopService(None, None, None, None, None) # type: ignore
    assert service._determine_risk_tier("GITHUB_REPOSITORY_READ") == RiskTier.READ_ONLY
    assert service._determine_risk_tier("GITHUB_ISSUE_CREATE") == RiskTier.LOW_RISK_MUTATION
    assert service._determine_risk_tier("EMAIL_SEND") == RiskTier.HIGH_RISK_MUTATION
    assert service._determine_risk_tier(None) == RiskTier.READ_ONLY

def test_evaluate_policy():
    service = AutonomousLoopService(None, None, None, None, None) # type: ignore
    assert service._evaluate_policy(AutonomyMode.MANUAL, RiskTier.READ_ONLY) == PolicyDecision.REQUIRE_APPROVAL
    assert service._evaluate_policy(AutonomyMode.AUTONOMOUS_WITHIN_POLICY, RiskTier.READ_ONLY) == PolicyDecision.ALLOW
    assert service._evaluate_policy(AutonomyMode.AUTONOMOUS_WITHIN_POLICY, RiskTier.SENSITIVE) == PolicyDecision.REQUIRE_APPROVAL



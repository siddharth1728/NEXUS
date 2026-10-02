import uuid
import pytest
from unittest.mock import AsyncMock, MagicMock
from app.services.verification_service import VerificationService
from app.schemas.verification import EvidenceRequirementCreate
from app.models.enums import Capability
from app.core.execution.tool_registry import ToolRegistry
from pydantic import BaseModel

class DummyInput(BaseModel):
    issue_number: int

class DummyTool:
    tool_id = "dummy_tool"
    capability = Capability.GITHUB_ISSUE_READ

    def get_input_schema(self):
        return DummyInput

    async def execute(self, params, context):
        return {"state": "open", "title": "Test Issue"}

@pytest.fixture
def mock_tool_registry():
    registry = MagicMock(spec=ToolRegistry)
    tool = DummyTool()
    registry.get.return_value = tool
    return registry

@pytest.fixture
def verification_service(in_memory_db_session, mock_tool_registry):
    return VerificationService(in_memory_db_session, mock_tool_registry)

from app.models.tenant import Tenant
from app.models.action import Action
from app.models.enums import ActionStatus

@pytest.fixture
async def sample_action(in_memory_db_session):
    tenant = Tenant(name="Test Tenant")
    in_memory_db_session.add(tenant)
    await in_memory_db_session.commit()
    await in_memory_db_session.refresh(tenant)

    action = Action(
        tenant_id=tenant.id,
        title="Test Action",
        description="Test Description",
        status=ActionStatus.PENDING_VERIFICATION,
    )
    in_memory_db_session.add(action)
    await in_memory_db_session.commit()
    await in_memory_db_session.refresh(action)
    return tenant, action

@pytest.mark.asyncio
async def test_create_requirement(verification_service, sample_action):
    tenant, action = sample_action
    req_data = EvidenceRequirementCreate(
        action_id=action.id,
        tool_id="dummy_tool",
        parameters={"issue_number": 1},
        expected_state={"state": "open"}
    )
    req = await verification_service.create_requirement(str(tenant.id), req_data)
    assert req.tool_id == "dummy_tool"
    assert req.expected_state == {"state": "open"}

@pytest.mark.asyncio
async def test_verify_requirement_success(verification_service, sample_action):
    tenant, action = sample_action
    req_data = EvidenceRequirementCreate(
        action_id=action.id,
        tool_id="dummy_tool",
        parameters={"issue_number": 1},
        expected_state={"state": "open"}
    )
    req = await verification_service.create_requirement(str(tenant.id), req_data)
    
    result = await verification_service.verify_requirement(str(tenant.id), str(req.id))
    assert result.is_verified is True
    assert result.evidence_id is not None

@pytest.mark.asyncio
async def test_verify_requirement_failure(verification_service, sample_action):
    tenant, action = sample_action
    req_data = EvidenceRequirementCreate(
        action_id=action.id,
        tool_id="dummy_tool",
        parameters={"issue_number": 1},
        expected_state={"state": "closed"}
    )
    req = await verification_service.create_requirement(str(tenant.id), req_data)
    
    result = await verification_service.verify_requirement(str(tenant.id), str(req.id))
    assert result.is_verified is False
    assert result.evidence_id is not None

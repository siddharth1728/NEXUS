import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.models.enums import ActionStatus
from app.services.action_service import ActionService
from app.services.workflow_service import WorkflowEngine


@pytest.fixture
def mock_action_service():
    return MagicMock(spec=ActionService)

@pytest.fixture
def workflow_engine(in_memory_db_session, mock_action_service):
    return WorkflowEngine(in_memory_db_session, mock_action_service)

@pytest.mark.asyncio
async def test_evaluate_dependencies_all_resolved(workflow_engine, mock_action_service):
    tenant_id = str(uuid.uuid4())
    action_id = str(uuid.uuid4())

    edge = MagicMock()
    edge.target_id = uuid.uuid4()
    mock_action_service.get_dependencies = AsyncMock(return_value=([edge], 1))

    target_action = MagicMock()
    target_action.status = ActionStatus.VERIFIED

    main_action = MagicMock()
    main_action.status = ActionStatus.BLOCKED

    mock_action_service.get_action = AsyncMock(side_effect=[target_action, main_action])
    mock_action_service.transition_state = AsyncMock()

    await workflow_engine.evaluate_dependencies(tenant_id, action_id)

    mock_action_service.transition_state.assert_called_once_with(uuid.UUID(action_id), uuid.UUID(tenant_id), ActionStatus.READY)

@pytest.mark.asyncio
async def test_evaluate_dependencies_not_resolved(workflow_engine, mock_action_service):
    tenant_id = str(uuid.uuid4())
    action_id = str(uuid.uuid4())

    edge = MagicMock()
    edge.target_id = uuid.uuid4()
    mock_action_service.get_dependencies = AsyncMock(return_value=([edge], 1))

    target_action = MagicMock()
    target_action.status = ActionStatus.IN_PROGRESS

    main_action = MagicMock()
    main_action.status = ActionStatus.READY

    mock_action_service.get_action = AsyncMock(side_effect=[target_action, main_action])
    mock_action_service.transition_state = AsyncMock()

    await workflow_engine.evaluate_dependencies(tenant_id, action_id)

    mock_action_service.transition_state.assert_called_once_with(uuid.UUID(action_id), uuid.UUID(tenant_id), ActionStatus.BLOCKED)

@pytest.mark.asyncio
async def test_process_verification_result_success(workflow_engine, mock_action_service):
    tenant_id = str(uuid.uuid4())
    action_id = str(uuid.uuid4())

    mock_action_service.get_action = AsyncMock()
    mock_action_service.transition_state = AsyncMock()
    mock_action_service.get_dependents = AsyncMock(return_value=([], 0))

    await workflow_engine.process_verification_result(tenant_id, action_id, True, "Success")

    mock_action_service.transition_state.assert_called_once_with(uuid.UUID(action_id), uuid.UUID(tenant_id), ActionStatus.VERIFIED)

@pytest.mark.asyncio
async def test_process_verification_result_failure(workflow_engine, mock_action_service):
    tenant_id = str(uuid.uuid4())
    action_id = str(uuid.uuid4())

    mock_action_service.get_action = AsyncMock()
    mock_action_service.transition_state = AsyncMock()

    await workflow_engine.process_verification_result(tenant_id, action_id, False, "Failed")

    mock_action_service.transition_state.assert_called_once_with(uuid.UUID(action_id), uuid.UUID(tenant_id), ActionStatus.REQUIRES_REVIEW)

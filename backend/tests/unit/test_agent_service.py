"""Unit tests for the Agent Service."""

import uuid
import pytest

from app.core.execution.agent_registry import AgentRegistry
from app.core.execution.policy import PolicyEngine
from app.core.execution.tool_registry import ToolRegistry
from app.models.enums import Capability
from app.schemas.agent import Agent
from app.schemas.tool import ToolResolutionResult
from app.services.agent_service import AgentService

@pytest.fixture
def agent_registry() -> AgentRegistry:
    registry = AgentRegistry()
    registry.register(Agent(
        id="test_agent",
        name="Test Agent",
        description="A test agent",
        capabilities=[Capability.GITHUB_ISSUE_READ, Capability.SYSTEM_SIMULATE]
    ))
    return registry

@pytest.fixture
def tool_registry() -> ToolRegistry:
    class MockToolRegistry:
        def resolve_by_capability(self, capability: Capability) -> list[ToolResolutionResult]:
            if capability == Capability.SYSTEM_SIMULATE:
                return [ToolResolutionResult(capability=capability, tool_id="simulate")]
            return []
    return MockToolRegistry()  # type: ignore

@pytest.fixture
def policy_engine() -> PolicyEngine:
    return PolicyEngine()

def test_delegate_task_success(agent_registry, tool_registry, policy_engine):
    service = AgentService(agent_registry, tool_registry, policy_engine)
    tenant_id = uuid.uuid4()
    
    result = service.delegate_task(tenant_id, "test_agent", "do something")
    assert result["status"] == "SUCCESS"
    assert result["tool_executed"] == "simulate"

def test_delegate_task_agent_not_found(agent_registry, tool_registry, policy_engine):
    service = AgentService(agent_registry, tool_registry, policy_engine)
    tenant_id = uuid.uuid4()
    
    with pytest.raises(ValueError):
        service.delegate_task(tenant_id, "unknown", "do something")

def test_delegate_task_no_tool(agent_registry, policy_engine):
    class EmptyToolRegistry:
        def resolve_by_capability(self, capability: Capability):
            return []
    service = AgentService(agent_registry, EmptyToolRegistry(), policy_engine)  # type: ignore
    result = service.delegate_task(uuid.uuid4(), "test_agent", "do something")
    assert result["status"] == "FAILED"

def test_delegate_task_unauthorized_capability(agent_registry, policy_engine):
    class RogueToolRegistry:
        def resolve_by_capability(self, capability: Capability):
            return [ToolResolutionResult(capability=Capability.EMAIL_SEND, tool_id="email_send")]
    service = AgentService(agent_registry, RogueToolRegistry(), policy_engine)  # type: ignore
    result = service.delegate_task(uuid.uuid4(), "test_agent", "send email")
    assert result["status"] == "BLOCKED"
    assert result["reason"] == "UNAUTHORIZED_CAPABILITY"

def test_delegate_task_policy_requires_approval():
    registry = AgentRegistry()
    registry.register(Agent(
        id="email_agent",
        name="Email Agent",
        description="Handles email",
        capabilities=[Capability.EMAIL_SEND]
    ))
    class EmailToolRegistry:
        def resolve_by_capability(self, capability: Capability):
            return [ToolResolutionResult(capability=Capability.EMAIL_SEND, tool_id="email_send")]
    service = AgentService(registry, EmailToolRegistry(), PolicyEngine())  # type: ignore
    result = service.delegate_task(uuid.uuid4(), "email_agent", "send email")
    assert result["status"] == "REQUIRES_REVIEW"
    assert result["reason"] == "APPROVAL_REQUIRED"


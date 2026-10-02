"""Unit tests for the Execution Engine."""

import uuid
from typing import Any

import pytest
from pydantic import BaseModel, Field

from app.core.execution.agent_registry import AgentRegistry
from app.core.execution.policy import PolicyEngine
from app.core.execution.router import AgentRouter
from app.core.execution.tool import BaseTool
from app.core.execution.tool_registry import ToolRegistry
from app.models.enums import Capability, PolicyDecision
from app.schemas.agent import Agent
from app.schemas.execution import ExecutionRequestCreate


class DummyInput(BaseModel):
    foo: str = Field(...)

class DummyTool(BaseTool):
    @property
    def tool_id(self) -> str:
        return "dummy_tool"

    @property
    def capability(self) -> Capability:
        return Capability.EMAIL_SEND

    def get_input_schema(self) -> type[BaseModel]:
        return DummyInput

    async def execute(self, parameters: BaseModel, context: Any = None) -> dict[str, Any]:  # type: ignore[override]
        return {"foo": parameters.foo}  # type: ignore[attr-defined]


def test_agent_registry() -> None:
    registry = AgentRegistry()
    agent = Agent(id="test_agent", name="Test", description="Test", capabilities=[Capability.EMAIL_SEND])
    registry.register(agent)

    fetched = registry.get("test_agent")
    assert fetched is not None
    assert fetched.id == "test_agent"

    assert registry.get("nonexistent") is None


def test_tool_registry() -> None:
    registry = ToolRegistry()
    tool = DummyTool()
    registry.register(tool)

    fetched = registry.get("dummy_tool")
    assert fetched is not None
    assert fetched.tool_id == "dummy_tool"

    resolved = registry.resolve_by_capability(Capability.EMAIL_SEND)
    assert len(resolved) == 1
    assert resolved[0].tool_id == "dummy_tool"


def test_agent_router() -> None:
    registry = ToolRegistry()
    registry.register(DummyTool())
    router = AgentRouter(registry)

    result = router.resolve_intent("Please send an email")
    assert result is not None
    assert result.capability == Capability.EMAIL_SEND
    assert result.tool_id == "dummy_tool"

    result2 = router.resolve_intent("Make a calendar event")
    assert result2 is None  # Not registered


def test_policy_engine() -> None:
    engine = PolicyEngine()

    # ALLOW
    req = ExecutionRequestCreate(action_id=uuid.uuid4(), agent_id="test", capability=Capability.DOCUMENT_READ, tool_id="test", parameters={})
    assert engine.evaluate(req) == PolicyDecision.ALLOW

    # REQUIRE_APPROVAL
    req = ExecutionRequestCreate(action_id=uuid.uuid4(), agent_id="test", capability=Capability.EMAIL_SEND, tool_id="test", parameters={})
    assert engine.evaluate(req) == PolicyDecision.REQUIRE_APPROVAL

    # DENY unknown / default
    req = ExecutionRequestCreate(action_id=uuid.uuid4(), agent_id="test", capability=Capability.EMAIL_DRAFT, tool_id="test", parameters={})
    assert engine.evaluate(req) == PolicyDecision.DENY


@pytest.mark.asyncio
async def test_tool_execution() -> None:
    tool = DummyTool()

    # Valid execution
    params = DummyInput(foo="bar")
    res = await tool.execute(params)
    assert res == {"foo": "bar"}

"""Simulated Executor Tool."""

import asyncio
from typing import Any

from pydantic import BaseModel, Field

from app.core.execution.tool import BaseTool
from app.models.enums import Capability


class SimulatedToolInput(BaseModel):
    """Input schema for the simulated tool."""
    
    action_type: str = Field(description="The mock action to perform.")
    should_fail: bool = Field(default=False, description="Whether the mock should intentionally fail.")
    delay_ms: int = Field(default=0, description="Simulated network delay in milliseconds.")
    mock_payload: dict[str, Any] = Field(default_factory=dict, description="Mock data to return.")
    requires_approval: bool = Field(default=False, description="Whether this request should trigger the approval workflow.")


class SimulatedTool(BaseTool):
    """A deterministic, simulated tool for safe end-to-end testing."""
    
    @property
    def tool_id(self) -> str:
        return "simulate_v1"
        
    @property
    def capability(self) -> Capability:
        return Capability.SYSTEM_SIMULATE
        
    def get_input_schema(self) -> type[BaseModel]:
        return SimulatedToolInput
        
    async def execute(self, parameters: BaseModel) -> dict[str, Any]:
        """Execute the simulated action deterministically."""
        if not isinstance(parameters, SimulatedToolInput):
            raise TypeError("Invalid parameters type.")
            
        if parameters.delay_ms > 0:
            await asyncio.sleep(parameters.delay_ms / 1000.0)
            
        if parameters.should_fail:
            raise RuntimeError("Simulated intentional failure.")
            
        return {
            "status": "success",
            "action": parameters.action_type,
            "mock_data": parameters.mock_payload
        }

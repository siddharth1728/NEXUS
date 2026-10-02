"""Schemas for Action Execution."""

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import ApprovalDecision, Capability, ExecutionState, PolicyDecision


class ExecutionRequestCreate(BaseModel):
    """Payload to request the execution of an Action."""
    
    action_id: uuid.UUID = Field(description="The action intended to be executed.")
    agent_id: str = Field(description="The ID of the agent proposing the execution.")
    capability: Capability = Field(description="The capability required to execute.")
    tool_id: str = Field(description="The tool ID requested.")
    parameters: dict[str, Any] = Field(default_factory=dict, description="Parameters for the tool execution.")


class ExecutionResponse(BaseModel):
    """Normalized response of an Execution record."""
    
    id: uuid.UUID
    tenant_id: uuid.UUID
    action_id: uuid.UUID
    requester_id: uuid.UUID | None = None
    agent_id: str
    capability: Capability
    tool_id: str
    parameters: dict[str, Any]
    state: ExecutionState
    
    policy_decision: PolicyDecision | None = None
    approval_decision: ApprovalDecision | None = None
    approver_id: uuid.UUID | None = None
    approval_reason: str | None = None
    
    result_payload: dict[str, Any] | None = None
    error_message: str | None = None
    
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class ExecutionApproval(BaseModel):
    """Payload for human or system approval."""
    
    decision: ApprovalDecision
    reason: str | None = None


class DryRunResult(BaseModel):
    """Output format for dry-run executions."""
    
    action_id: uuid.UUID
    agent_id: str
    capability: Capability
    tool_id: str
    parameters: dict[str, Any]
    policy_decision: PolicyDecision
    would_execute: bool
    reason: str | None = None

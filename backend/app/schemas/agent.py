"""Schemas for Agent Model."""

from typing import Any

from pydantic import BaseModel, Field

from app.models.enums import Capability


class Agent(BaseModel):
    """Normalized NEXUS Agent definition."""
    
    id: str = Field(description="Unique identifier for the agent (e.g., 'planner', 'approval_assistant').")
    name: str = Field(description="Human-readable name.")
    description: str = Field(description="Role and responsibility description.")
    capabilities: list[Capability] = Field(default_factory=list, description="Capabilities this agent is permitted to request.")
    version: str = Field(default="1.0.0")
    config_metadata: dict[str, Any] = Field(default_factory=dict, description="Configuration metadata.")

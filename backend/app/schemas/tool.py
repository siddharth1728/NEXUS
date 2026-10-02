"""Schemas for Tool Abstraction."""

from pydantic import BaseModel, Field

from app.models.enums import Capability


class ToolResolutionResult(BaseModel):
    """Result of mapping an intent to a tool."""
    
    capability: Capability = Field(description="The resolved capability.")
    tool_id: str = Field(description="The ID of the tool chosen to fulfill the capability.")

"""Tool Abstraction for Action Execution."""

from abc import ABC, abstractmethod
from typing import Any

from pydantic import BaseModel

from app.models.enums import Capability


class BaseTool(ABC):
    """NEXUS Tool Abstraction.
    
    A tool represents a discrete unit of capability that an agent can invoke.
    Tools must declare strict input schemas and capabilities.
    """
    
    @property
    @abstractmethod
    def tool_id(self) -> str:
        """Unique identifier for this tool (e.g., 'email_sender_v1')."""
        pass
        
    @property
    @abstractmethod
    def capability(self) -> Capability:
        """The capability required to execute this tool."""
        pass
        
    @property
    def version(self) -> str:
        """Semantic version of the tool."""
        return "1.0.0"
        
    @abstractmethod
    def get_input_schema(self) -> type[BaseModel]:
        """Returns the strict Pydantic schema for inputs."""
        pass
        
    @abstractmethod
    async def execute(self, parameters: BaseModel) -> dict[str, Any]:
        """Execute the tool with the validated parameters.
        
        Args:
            parameters: An instance of the model returned by get_input_schema().
            
        Returns:
            A JSON-serializable dictionary containing the execution result.
        """
        pass

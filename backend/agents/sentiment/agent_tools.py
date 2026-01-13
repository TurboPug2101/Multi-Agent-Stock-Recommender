"""
Agent Tools Registry
Defines tools that the sentiment agent can call autonomously.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class Tool:
    """Represents a tool that an agent can call."""
    name: str
    description: str
    parameters: Dict[str, Any]  # JSON schema for parameters
    function: Callable
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert tool to dictionary for LLM function calling."""
        return {
            "name": self.name,
            "description": self.description,
            "parameters": self.parameters
        }


class ToolRegistry:
    """Registry of available tools for agents."""
    
    def __init__(self):
        self.tools: Dict[str, Tool] = {}
    
    def register(self, tool: Tool):
        """Register a tool."""
        self.tools[tool.name] = tool
        logger.debug(f"Registered tool: {tool.name}")
    
    def get_tool(self, name: str) -> Optional[Tool]:
        """Get a tool by name."""
        return self.tools.get(name)
    
    def list_tools(self) -> List[Dict[str, Any]]:
        """List all available tools as dictionaries."""
        return [tool.to_dict() for tool in self.tools.values()]
    
    def call_tool(self, name: str, **kwargs) -> Any:
        """Call a tool by name with arguments."""
        tool = self.get_tool(name)
        if not tool:
            raise ValueError(f"Tool '{name}' not found")
        
        logger.info(f"Agent calling tool: {name} with args: {kwargs}")
        try:
            result = tool.function(**kwargs)
            logger.info(f"Tool {name} executed successfully")
            return result
        except Exception as e:
            logger.error(f"Error calling tool {name}: {e}", exc_info=True)
            raise

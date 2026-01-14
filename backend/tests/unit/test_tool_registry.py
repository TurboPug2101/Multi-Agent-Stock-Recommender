"""
Unit tests for Tool Registry.
"""

import pytest
from agents.sentiment.agent_tools import ToolRegistry, Tool


@pytest.mark.unit
class TestToolRegistry:
    """Test Tool Registry functionality."""
    
    def test_tool_registration_and_retrieval(self):
        """Test registering and retrieving tools."""
        registry = ToolRegistry()
        
        # Create a mock tool
        def mock_function(symbol, days=14):
            return [f"Article about {symbol}"]
        
        tool = Tool(
            name="fetch_news",
            description="Fetch news articles",
            parameters={"type": "object", "properties": {"symbol": {"type": "string"}}},
            function=mock_function
        )
        
        # Register tool
        registry.register(tool)
        
        # Retrieve tool
        retrieved = registry.get_tool("fetch_news")
        assert retrieved is not None
        assert retrieved.name == "fetch_news"
        assert retrieved.description == "Fetch news articles"
    
    def test_tool_calling(self):
        """Test calling a registered tool."""
        registry = ToolRegistry()
        
        # Create and register a tool
        def add_numbers(a, b):
            return a + b
        
        tool = Tool(
            name="add",
            description="Add two numbers",
            parameters={"type": "object"},
            function=add_numbers
        )
        registry.register(tool)
        
        # Call the tool
        result = registry.call_tool("add", a=5, b=3)
        assert result == 8
        
        # Test calling non-existent tool
        with pytest.raises(ValueError, match="Tool 'nonexistent' not found"):
            registry.call_tool("nonexistent")

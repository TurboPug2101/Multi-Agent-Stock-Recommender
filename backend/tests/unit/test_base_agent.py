"""
Unit tests for BaseAgent contract.
"""

import pytest
from unittest.mock import Mock
from common.base_agent import BaseAgent


class MockAgent(BaseAgent):
    """Mock agent for testing BaseAgent."""
    
    def validate_input(self, input_data):
        """Mock validation."""
        return 'valid' in input_data
    
    def run(self, input_data):
        """Mock run method."""
        return {'result': 'success', 'input': input_data}


@pytest.mark.unit
class TestBaseAgent:
    """Test BaseAgent contract."""
    
    def test_base_agent_contract(self):
        """Test that BaseAgent enforces contract methods."""
        agent = MockAgent(agent_name="test_agent")
        
        # Test agent has required methods
        assert hasattr(agent, 'validate_input')
        assert hasattr(agent, 'run')
        assert hasattr(agent, 'execute')
        assert agent.agent_name == "test_agent"
    
    def test_execute_with_validation_and_error_handling(self):
        """Test execute method with validation and error handling."""
        agent = MockAgent(agent_name="test_agent")
        
        # Test successful execution
        result = agent.execute({'valid': True})
        assert result['status'] == 'success'
        assert result['agent'] == 'test_agent'
        assert result['data'] == {'result': 'success', 'input': {'valid': True}}
        assert result['error'] is None
        
        # Test validation failure
        result = agent.execute({'invalid': True})
        assert result['status'] == 'error'
        assert result['error'] == 'Invalid input data'
        assert result['data'] is None

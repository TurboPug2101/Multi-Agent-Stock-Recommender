"""
Tests for Technical Agent.
"""

import pytest
from agents.technical.technical_agent import TechnicalAgent
from agents.technical.technical_schemas import TechnicalAgentInput


@pytest.mark.unit
class TestTechnicalAgent:
    """Test TechnicalAgent functionality."""
    
    def test_technical_agent_analysis(self, mock_data_provider, sample_technical_input):
        """Test technical analysis on stocks."""
        agent = TechnicalAgent(data_provider=mock_data_provider)
        
        # Execute agent
        result = agent.run(sample_technical_input)
        
        # Verify output structure
        assert 'technical_signals' in result
        assert isinstance(result['technical_signals'], list)
        
        # Verify signals have required fields
        if result['technical_signals']:
            signal = result['technical_signals'][0]
            assert 'symbol' in signal
            assert 'signal' in signal or 'action' in signal
    
    def test_technical_agent_input_validation(self, mock_data_provider):
        """Test technical agent input validation."""
        agent = TechnicalAgent(data_provider=mock_data_provider)
        
        # Valid input
        valid_input = {"stocks": ["RELIANCE.NS"]}
        assert agent.validate_input(valid_input) is True
        
        # Invalid input - missing stocks
        invalid_input = {}
        assert agent.validate_input(invalid_input) is False

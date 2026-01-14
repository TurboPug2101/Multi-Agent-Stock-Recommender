"""
Tests for Strategist Agent.
"""

import pytest
from unittest.mock import patch, MagicMock
from agents.strategist.agent import StrategistAgent


@pytest.mark.unit
class TestStrategistAgent:
    """Test StrategistAgent functionality."""
    
    @patch('agents.strategist.agent.Groq')
    @patch('agents.strategist.agent.KiteClient')
    def test_strategist_agent_initialization(self, mock_kite_class, mock_groq_class, 
                                             mock_environment_variables):
        """Test strategist agent initialization."""
        agent = StrategistAgent()
        
        assert agent is not None
        assert hasattr(agent, 'groq_client')
        assert hasattr(agent, 'kite_client')
    
    @patch('agents.strategist.agent.Groq')
    @patch('agents.strategist.agent.KiteClient')
    def test_strategist_agent_decision_making(self, mock_kite_class, mock_groq_class,
                                               sample_strategist_input, mock_environment_variables):
        """Test strategist agent decision making."""
        # Setup mocks
        mock_groq = MagicMock()
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message = MagicMock()
        mock_response.choices[0].message.content = '{"decisions": [{"symbol": "RELIANCE.NS", "action": "BUY", "confidence": 0.82}]}'
        mock_groq.chat.completions.create.return_value = mock_response
        mock_groq_class.return_value = mock_groq
        
        mock_kite = MagicMock()
        mock_kite.place_order.return_value = {"order_id": "TEST123"}
        mock_kite_class.return_value = mock_kite
        
        agent = StrategistAgent()
        
        # Execute agent
        result = agent.run(sample_strategist_input)
        
        # Verify output structure
        assert 'trading_decisions' in result or 'decisions' in result

"""
Tests for Scouting Agent.
"""

import pytest
from unittest.mock import patch, MagicMock
from agents.scouting.agent import ScoutingAgent
from agents.scouting.schemas import ScoutingAgentInput, StockScreeningResult


@pytest.mark.unit
class TestScoutingAgent:
    """Test ScoutingAgent functionality."""
    
    @patch('agents.scouting.agent.get_nifty50_symbols')
    @patch('agents.scouting.agent.screen_stocks')
    @patch('agents.scouting.agent.shortlist_stocks')
    def test_scouting_agent_screening(self, mock_shortlist, mock_screen, mock_nifty50,
                                     mock_data_provider, sample_scouting_input):
        """Test stock screening and shortlisting."""
        # Setup mocks
        mock_nifty50.return_value = ["RELIANCE.NS", "TCS.NS"]
        mock_screen.return_value = [
            StockScreeningResult(
                symbol="RELIANCE.NS",
                name="Reliance",
                current_price=2450.0,
                atr_percentage=2.5,
                avg_volume=5000000,
                recent_volume=6000000,
                volume_ratio=1.2,
                meets_criteria=True,
                criteria_details=[],
                score=85.0
            )
        ]
        mock_shortlist.return_value = mock_screen.return_value[:1]
        
        agent = ScoutingAgent(data_provider=mock_data_provider)
        
        # Execute agent
        result = agent.run(sample_scouting_input)
        
        # Verify output structure
        assert 'shortlisted_stocks' in result
        assert 'total_screened' in result
        assert 'qualifying_count' in result
        assert isinstance(result['shortlisted_stocks'], list)
    
    @patch('agents.scouting.agent.get_nifty50_symbols')
    @patch('agents.scouting.agent.screen_stocks')
    @patch('agents.scouting.agent.shortlist_stocks')
    def test_scouting_agent_caching(self, mock_shortlist, mock_screen, mock_nifty50,
                                   mock_data_provider, sample_scouting_input, isolated_cache):
        """Test that scouting agent uses caching."""
        # Setup mocks
        mock_nifty50.return_value = ["RELIANCE.NS"]
        mock_screen.return_value = [
            StockScreeningResult(
                symbol="RELIANCE.NS",
                name="Reliance",
                current_price=2450.0,
                atr_percentage=2.5,
                avg_volume=5000000,
                recent_volume=6000000,
                volume_ratio=1.2,
                meets_criteria=True,
                criteria_details=[],
                score=85.0
            )
        ]
        mock_shortlist.return_value = mock_screen.return_value
        
        agent = ScoutingAgent(data_provider=mock_data_provider)
        
        # First execution - should call data provider
        result1 = agent.run(sample_scouting_input)
        
        # Second execution with same input - should use cache
        result2 = agent.run(sample_scouting_input)
        
        # Both should have same structure
        assert 'shortlisted_stocks' in result1
        assert 'shortlisted_stocks' in result2
        # Verify nifty50 was only called once (second call uses cache)
        assert mock_nifty50.call_count == 1

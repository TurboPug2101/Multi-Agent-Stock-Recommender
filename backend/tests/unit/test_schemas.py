"""
Unit tests for Pydantic schemas.
"""

import pytest
from agents.scouting.schemas import ScoutingAgentInput, ScoutingAgentOutput, StockScreeningResult


@pytest.mark.unit
class TestSchemas:
    """Test schema validation."""
    
    def test_scouting_agent_input_validation(self):
        """Test ScoutingAgentInput validation."""
        # Valid input
        valid_input = ScoutingAgentInput(top_n=10)
        assert valid_input.validate() is True
        
        # Invalid input - top_n too high
        invalid_input = ScoutingAgentInput(top_n=100)
        assert invalid_input.validate() is False
        
        # Invalid input - top_n too low
        invalid_input2 = ScoutingAgentInput(top_n=0)
        assert invalid_input2.validate() is False
    
    def test_stock_screening_result_to_dict(self):
        """Test StockScreeningResult serialization."""
        result = StockScreeningResult(
            symbol="RELIANCE.NS",
            name="Reliance Industries",
            current_price=2450.50,
            atr_percentage=2.5,
            avg_volume=5000000,
            recent_volume=6000000,
            volume_ratio=1.2,
            meets_criteria=True,
            criteria_details=["High liquidity"],
            score=85.5
        )
        
        result_dict = result.to_dict()
        assert result_dict['symbol'] == "RELIANCE.NS"
        assert result_dict['current_price'] == 2450.50
        assert result_dict['score'] == 85.5
        assert isinstance(result_dict['criteria_details'], list)

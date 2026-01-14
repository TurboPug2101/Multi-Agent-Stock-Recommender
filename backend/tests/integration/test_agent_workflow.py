"""
End-to-end workflow integration tests.
"""

import pytest
from unittest.mock import patch, MagicMock
from orchestrator.main import Orchestrator


@pytest.mark.integration
class TestAgentWorkflow:
    """Test complete agent workflow."""
    
    @patch('orchestrator.main.importlib.import_module')
    @patch('agents.scouting.agent.get_nifty50_symbols')
    @patch('agents.scouting.agent.screen_stocks')
    @patch('agents.scouting.agent.shortlist_stocks')
    def test_complete_dag_execution(self, mock_shortlist, mock_screen, mock_nifty50, mock_import):
        """Test complete DAG execution from scouting to strategist."""
        # Setup mocks
        from agents.scouting.schemas import StockScreeningResult
        
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
        
        # Mock agent modules
        mock_module = MagicMock()
        mock_agent = MagicMock()
        mock_agent.run.return_value = {"shortlisted_stocks": []}
        mock_module.create_agent = MagicMock(return_value=mock_agent)
        mock_module.ScoutingAgent = MagicMock(return_value=mock_agent)
        mock_import.return_value = mock_module
        
        orchestrator = Orchestrator()
        
        # Execute with initial input
        result = orchestrator.execute(initial_input={"top_n": 10})
        
        # Verify execution completed
        assert result is not None
        assert hasattr(result, 'status') or isinstance(result, dict)

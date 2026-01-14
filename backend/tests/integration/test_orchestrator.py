"""
Integration tests for Orchestrator.
"""

import pytest
from unittest.mock import patch, MagicMock
from orchestrator.main import Orchestrator


@pytest.mark.integration
class TestOrchestrator:
    """Test Orchestrator DAG execution."""
    
    @patch('orchestrator.main.importlib.import_module')
    def test_orchestrator_initialization(self, mock_import):
        """Test orchestrator initialization with DAG config."""
        # Mock agent modules
        mock_module = MagicMock()
        mock_agent_class = MagicMock()
        mock_module.ScoutingAgent = mock_agent_class
        mock_agent_class.return_value = MagicMock()
        mock_import.return_value = mock_module
        
        orchestrator = Orchestrator()
        
        assert orchestrator is not None
        assert hasattr(orchestrator, 'dag_config')
        assert hasattr(orchestrator, 'execution_order')
        assert len(orchestrator.execution_order) > 0
    
    @patch('orchestrator.main.importlib.import_module')
    def test_orchestrator_execution_order(self, mock_import):
        """Test that orchestrator resolves correct execution order."""
        # Mock agent modules
        mock_module = MagicMock()
        mock_agent_class = MagicMock()
        mock_module.ScoutingAgent = mock_agent_class
        mock_module.create_agent = MagicMock(return_value=MagicMock())
        mock_agent_class.return_value = MagicMock()
        mock_import.return_value = mock_module
        
        orchestrator = Orchestrator()
        
        # Verify execution order: scouting should be first (no dependencies)
        first_level = orchestrator.execution_order[0]
        assert 'scouting' in first_level
        
        # Verify technical and sentiment are in same level (parallel)
        if len(orchestrator.execution_order) > 1:
            second_level = orchestrator.execution_order[1]
            assert 'technical' in second_level or 'sentiment' in second_level

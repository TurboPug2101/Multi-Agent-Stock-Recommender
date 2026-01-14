"""
Tests for Sentiment Agent.
"""

import pytest
from unittest.mock import patch, MagicMock
from agents.sentiment.sentiment_agent import SentimentAgent


@pytest.mark.unit
class TestSentimentAgent:
    """Test SentimentAgent functionality."""
    
    @patch('agents.sentiment.sentiment_agent.Groq')
    def test_sentiment_agent_initialization(self, mock_groq_class, mock_environment_variables):
        """Test sentiment agent initialization with Groq client."""
        agent = SentimentAgent()
        
        assert agent is not None
        assert hasattr(agent, 'groq_client')
        assert hasattr(agent, 'tool_registry')
    
    @patch('agents.sentiment.sentiment_agent.Groq')
    @patch('agents.sentiment.social_media_tools.fetch_news')
    @patch('agents.sentiment.sentiment_tools.analyze_sentiment_with_groq')
    def test_sentiment_agent_execution(self, mock_analyze, mock_fetch_news, mock_groq_class, 
                                       sample_sentiment_input, mock_environment_variables):
        """Test sentiment agent execution with mocked dependencies."""
        # Setup mocks
        mock_fetch_news.return_value = []
        mock_analyze.return_value = {
            "overall_sentiment": "positive",
            "sentiment_score": 0.75,
            "confidence": 0.85
        }
        
        agent = SentimentAgent()
        
        # Execute agent
        result = agent.run(sample_sentiment_input)
        
        # Verify output structure
        assert 'analyzed_stocks' in result
        assert isinstance(result['analyzed_stocks'], list)

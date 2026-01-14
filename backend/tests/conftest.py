"""
Shared pytest fixtures and configuration.
"""

import os
import pytest
from unittest.mock import Mock, MagicMock, patch
from typing import Dict, Any
import pandas as pd
from datetime import datetime

# Import project modules
from common.cache import Cache
from agents.scouting.data_provider import StockDataProvider
from tests.fixtures.mock_data import (
    create_mock_historical_data,
    create_mock_stock_info,
    SAMPLE_NIFTY50_SYMBOLS,
    SAMPLE_SHORTLISTED_STOCKS
)
from tests.fixtures.mock_responses import (
    create_mock_groq_sentiment_response,
    create_mock_groq_decision_response,
    create_mock_groq_data_sufficiency_response,
    create_mock_news_api_response,
    create_mock_kite_order_response
)


# Check if real APIs should be used (for integration testing)
USE_REAL_APIS = os.getenv("USE_REAL_APIS", "false").lower() == "true"


@pytest.fixture
def isolated_cache():
    """Provide an isolated cache instance for each test."""
    return Cache()


@pytest.fixture
def mock_data_provider():
    """Mock StockDataProvider."""
    provider = Mock(spec=StockDataProvider)
    
    # Mock fetch_historical_data
    provider.fetch_historical_data.return_value = create_mock_historical_data()
    
    # Mock fetch_stock_info
    provider.fetch_stock_info.return_value = create_mock_stock_info()
    
    return provider


@pytest.fixture
def mock_groq_client():
    """Mock Groq client."""
    client = Mock()
    
    # Mock chat.completions.create
    mock_response = Mock()
    mock_response.choices = [Mock()]
    mock_response.choices[0].message = Mock()
    mock_response.choices[0].message.content = create_mock_groq_sentiment_response()
    
    client.chat.completions.create.return_value = mock_response
    
    return client


@pytest.fixture
def mock_groq_client_decision():
    """Mock Groq client for decision making."""
    client = Mock()
    
    mock_response = Mock()
    mock_response.choices = [Mock()]
    mock_response.choices[0].message = Mock()
    mock_response.choices[0].message.content = create_mock_groq_decision_response()
    
    client.chat.completions.create.return_value = mock_response
    
    return client


@pytest.fixture
def mock_groq_client_data_sufficiency():
    """Mock Groq client for data sufficiency reasoning."""
    client = Mock()
    
    mock_response = Mock()
    mock_response.choices = [Mock()]
    mock_response.choices[0].message = Mock()
    mock_response.choices[0].message.content = create_mock_groq_data_sufficiency_response(sufficient=False)
    
    client.chat.completions.create.return_value = mock_response
    
    return client


@pytest.fixture
def mock_kite_client():
    """Mock Kite client."""
    client = Mock()
    client.place_order.return_value = create_mock_kite_order_response()
    client.paper_trading = True
    return client


@pytest.fixture
def sample_scouting_input():
    """Sample input for scouting agent."""
    return {"top_n": 10}


@pytest.fixture
def sample_scouting_output():
    """Sample output from scouting agent."""
    return {
        "shortlisted_stocks": SAMPLE_SHORTLISTED_STOCKS,
        "total_screened": 50,
        "qualifying_count": 10,
        "criteria": {
            "min_volume": 1000000,
            "min_atr": 1.0
        }
    }


@pytest.fixture
def sample_technical_input():
    """Sample input for technical agent."""
    return {
        "stocks": ["RELIANCE.NS", "TCS.NS"]
    }


@pytest.fixture
def sample_technical_output():
    """Sample output from technical agent."""
    return {
        "technical_signals": [
            {
                "symbol": "RELIANCE.NS",
                "signal": "BUY",
                "confidence": 0.75,
                "indicators": {
                    "rsi": 55.0,
                    "macd": 12.5,
                    "sma_50": 2400.0
                }
            }
        ]
    }


@pytest.fixture
def sample_sentiment_input():
    """Sample input for sentiment agent."""
    return {
        "stocks": [
            {"symbol": "RELIANCE.NS", "name": "Reliance Industries Ltd"},
            {"symbol": "TCS.NS", "name": "Tata Consultancy Services"}
        ]
    }


@pytest.fixture
def sample_sentiment_output():
    """Sample output from sentiment agent."""
    return {
        "analyzed_stocks": [
            {
                "symbol": "RELIANCE.NS",
                "name": "Reliance Industries Ltd",
                "overall_sentiment": "positive",
                "sentiment_score": 0.75,
                "confidence": 0.85
            }
        ],
        "total_analyzed": 2,
        "positive_count": 1,
        "negative_count": 0,
        "neutral_count": 1
    }


@pytest.fixture
def sample_strategist_input():
    """Sample input for strategist agent."""
    return {
        "technical": {
            "technical_signals": [
                {
                    "symbol": "RELIANCE.NS",
                    "signal": "BUY",
                    "confidence": 0.75
                }
            ]
        },
        "sentiment": {
            "analyzed_stocks": [
                {
                    "symbol": "RELIANCE.NS",
                    "overall_sentiment": "positive",
                    "sentiment_score": 0.75
                }
            ]
        }
    }


@pytest.fixture
def mock_news_api(monkeypatch):
    """Mock news API calls."""
    if USE_REAL_APIS:
        return None
    
    def mock_fetch_news(*args, **kwargs):
        from tests.fixtures.mock_responses import create_mock_news_api_response
        return create_mock_news_api_response(article_count=10)
    
    # Mock the news provider
    monkeypatch.setattr(
        "agents.sentiment.social_media_tools._default_news_provider.fetch_news",
        lambda *args, **kwargs: []
    )
    
    return mock_fetch_news


@pytest.fixture
def mock_reddit_api(monkeypatch):
    """Mock Reddit API calls."""
    if USE_REAL_APIS:
        return None
    
    def mock_fetch_reddit(*args, **kwargs):
        from tests.fixtures.mock_data import create_mock_reddit_mentions
        return create_mock_reddit_mentions(count=5)
    
    monkeypatch.setattr(
        "agents.sentiment.social_media_tools.fetch_reddit_mentions",
        mock_fetch_reddit
    )
    
    return mock_fetch_reddit


@pytest.fixture(autouse=True)
def reset_cache():
    """Reset global cache before each test."""
    from common.cache import _cache
    _cache._cache.clear()
    yield
    _cache._cache.clear()


@pytest.fixture
def mock_environment_variables(monkeypatch):
    """Mock environment variables for testing."""
    monkeypatch.setenv("GROQ_API_KEY", "test_groq_key")
    monkeypatch.setenv("NEWS_API_KEY", "test_news_key")
    monkeypatch.setenv("NEWS_API_URL", "https://test-api.example.com")
    monkeypatch.setenv("KITE_API_KEY", "test_kite_key")
    monkeypatch.setenv("KITE_API_SECRET", "test_kite_secret")
    monkeypatch.setenv("KITE_ACCESS_TOKEN", "test_access_token")

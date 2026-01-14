"""
Mock API responses for testing.
"""

from typing import Dict, Any


def create_mock_groq_sentiment_response() -> str:
    """Create mock Groq LLM response for sentiment analysis."""
    return """{
        "overall_sentiment": "positive",
        "sentiment_score": 0.75,
        "confidence": 0.85,
        "summary_points": [
            "Positive news about earnings",
            "Strong market position",
            "Good analyst ratings"
        ],
        "key_insights": [
            "Company showing growth",
            "Market sentiment is favorable"
        ],
        "recommendation": "buy"
    }"""


def create_mock_groq_decision_response() -> str:
    """Create mock Groq LLM response for trading decision."""
    return """{
        "decisions": [
            {
                "symbol": "RELIANCE.NS",
                "action": "BUY",
                "confidence": 0.82,
                "reasoning": "Strong technical breakout with positive sentiment",
                "quantity": 10,
                "price": 2450.50
            }
        ]
    }"""


def create_mock_groq_data_sufficiency_response(sufficient: bool = False) -> str:
    """Create mock Groq LLM response for data sufficiency reasoning."""
    if sufficient:
        return """{
            "sufficient": true,
            "reasoning": "Adequate number of articles found for reliable sentiment analysis",
            "recommended_action": "proceed_with_analysis"
        }"""
    else:
        return """{
            "sufficient": false,
            "reasoning": "Only 5 articles found, need at least 10 for reliable sentiment",
            "recommended_action": "expand_timeframe",
            "suggested_days": 90
        }"""


def create_mock_news_api_response(article_count: int = 10) -> Dict[str, Any]:
    """Create mock Event Registry News API response."""
    articles = []
    for i in range(article_count):
        articles.append({
            "title": f"Financial News Article {i+1}",
            "body": f"This is the body of article {i+1}",
            "url": f"https://example.com/news/{i+1}",
            "date": "2024-01-01",
            "source": {
                "title": "Financial Times"
            }
        })
    
    return {
        "articles": {
            "results": articles
        },
        "articlesCount": article_count
    }


def create_mock_kite_order_response() -> Dict[str, Any]:
    """Create mock Kite API order response."""
    return {
        "order_id": "TEST123456",
        "status": "COMPLETE",
        "message": "Order placed successfully"
    }

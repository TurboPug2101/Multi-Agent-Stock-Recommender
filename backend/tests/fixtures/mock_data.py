"""
Mock data for testing.
"""

from typing import Dict, List, Any
import pandas as pd
import numpy as np
from datetime import datetime, timedelta


# Sample Nifty 50 symbols
SAMPLE_NIFTY50_SYMBOLS = [
    "RELIANCE.NS", "TCS.NS", "HDFCBANK.NS", "INFY.NS", "ICICIBANK.NS",
    "HINDUNILVR.NS", "SBIN.NS", "BHARTIARTL.NS", "KOTAKBANK.NS", "ITC.NS"
]

# Sample stock screening results
SAMPLE_SCREENING_RESULT = {
    "symbol": "RELIANCE.NS",
    "name": "Reliance Industries Ltd",
    "current_price": 2450.50,
    "atr_percentage": 2.5,
    "avg_volume": 5000000,
    "recent_volume": 6000000,
    "volume_ratio": 1.2,
    "meets_criteria": True,
    "criteria_details": ["High liquidity", "Good volume"],
    "score": 85.5
}

# Sample shortlisted stocks
SAMPLE_SHORTLISTED_STOCKS = [
    {
        "symbol": "RELIANCE.NS",
        "name": "Reliance Industries Ltd",
        "current_price": 2450.50,
        "atr_percentage": 2.5,
        "avg_volume": 5000000,
        "recent_volume": 6000000,
        "volume_ratio": 1.2,
        "meets_criteria": True,
        "criteria_details": ["High liquidity"],
        "score": 85.5
    },
    {
        "symbol": "TCS.NS",
        "name": "Tata Consultancy Services",
        "current_price": 3500.00,
        "atr_percentage": 1.8,
        "avg_volume": 3000000,
        "recent_volume": 3500000,
        "volume_ratio": 1.17,
        "meets_criteria": True,
        "criteria_details": ["Stable volume"],
        "score": 82.0
    }
]


def create_mock_historical_data(symbol: str = "RELIANCE.NS", days: int = 30) -> pd.DataFrame:
    """Create mock historical stock data."""
    dates = pd.date_range(end=datetime.now(), periods=days, freq='D')
    
    # Generate realistic-looking price data
    base_price = 2450.0
    prices = []
    for i in range(days):
        # Random walk with slight upward trend
        change = np.random.normal(0.5, 15)  # Mean 0.5, std 15
        base_price = max(base_price + change, 100)  # Don't go below 100
        prices.append(base_price)
    
    data = {
        'Open': [p * 0.99 for p in prices],
        'High': [p * 1.02 for p in prices],
        'Low': [p * 0.98 for p in prices],
        'Close': prices,
        'Volume': np.random.randint(1000000, 10000000, days)
    }
    
    df = pd.DataFrame(data, index=dates)
    return df


def create_mock_stock_info(symbol: str = "RELIANCE.NS") -> Dict[str, Any]:
    """Create mock stock information."""
    return {
        "symbol": symbol,
        "name": "Reliance Industries Ltd",
        "sector": "Energy",
        "market_cap": 16500000000000,  # 16.5T INR
        "current_price": 2450.50
    }


def create_mock_news_articles(count: int = 10) -> List[Dict[str, Any]]:
    """Create mock news articles."""
    articles = []
    for i in range(count):
        articles.append({
            "title": f"Stock Market News Article {i+1}",
            "description": f"This is a description of news article {i+1} about the stock market.",
            "published_date": (datetime.now() - timedelta(days=i)).isoformat(),
            "source": f"Financial News {i+1}"
        })
    return articles


def create_mock_reddit_mentions(count: int = 5) -> List[Dict[str, Any]]:
    """Create mock Reddit mentions."""
    mentions = []
    for i in range(count):
        mentions.append({
            "title": f"Reddit Discussion {i+1}",
            "content": f"This is a Reddit post about the stock.",
            "score": 100 + i * 10,
            "subreddit": "stocks",
            "created_utc": (datetime.now() - timedelta(days=i)).timestamp()
        })
    return mentions

"""
Sentiment Agent Schemas
Defines input and output contracts for the sentiment agent.
"""

from dataclasses import dataclass, asdict
from typing import Optional, List, Dict, Any


@dataclass
class NewsArticle:
    """Schema for a news article."""
    title: str
    description: Optional[str] = None
    published_date: Optional[str] = None
    source: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)


@dataclass
class SentimentAnalysisResult:
    """Sentiment analysis result for a single stock."""
    symbol: str
    name: str
    news_count: int
    summary_points: List[str]
    overall_sentiment: str  # 'very_positive', 'positive', 'neutral', 'negative', 'very_negative'
    sentiment_score: float  # -1.0 to 1.0
    confidence: float  # 0.0 to 1.0
    key_insights: List[str]
    recommendation: str  # 'strong_buy', 'buy', 'hold', 'sell', 'strong_sell'
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'symbol': self.symbol,
            'name': self.name,
            'news_count': self.news_count,
            'summary_points': self.summary_points,
            'overall_sentiment': self.overall_sentiment,
            'sentiment_score': self.sentiment_score,
            'confidence': self.confidence,
            'key_insights': self.key_insights,
            'recommendation': self.recommendation
        }


@dataclass
class SentimentAgentInput:
    """Input schema for Sentiment Agent."""
    stocks: List[Dict[str, Any]]  # List of stocks from scouting agent
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SentimentAgentInput':
        """Create from dictionary."""
        return cls(stocks=data.get('stocks', []))
    
    def validate(self) -> bool:
        """Validate input."""
        if not isinstance(self.stocks, list):
            return False
        if len(self.stocks) == 0:
            return False
        return True


@dataclass
class SentimentAgentOutput:
    """Output schema for Sentiment Agent."""
    analyzed_stocks: List[Dict[str, Any]]
    total_analyzed: int
    positive_count: int
    negative_count: int
    neutral_count: int
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)



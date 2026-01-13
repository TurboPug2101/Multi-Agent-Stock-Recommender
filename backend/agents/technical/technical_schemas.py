"""
Technical Agent Schemas
Defines input and output contracts for the technical agent.
"""

from dataclasses import dataclass, asdict
from typing import Optional, List, Dict, Any

@dataclass
class StockInput:
    """Single stock from scouting agent."""
    symbol: str
    name: str
    current_price: float
    atr_percentage: Optional[float] = None
    avg_volume: Optional[float] = None
    volume_ratio: Optional[float] = None
    meets_criteria: Optional[bool] = None

@dataclass
class TechnicalIndicators:
    """Technical analysis indicators for a stock."""
    rsi: Optional[float] = None  # Relative Strength Index (0-100)
    macd: Optional[float] = None  # MACD line
    macd_signal: Optional[float] = None  # Signal line
    macd_histogram: Optional[float] = None
    sma_20: Optional[float] = None  # 20-day Simple Moving Average
    sma_50: Optional[float] = None  # 50-day Simple Moving Average
    ema_12: Optional[float] = None  # 12-day Exponential Moving Average
    ema_26: Optional[float] = None  # 26-day Exponential Moving Average
    
    def to_dict(self):
        return asdict(self)

@dataclass
class TechnicalAnalysisResult:
    """Technical analysis result for a single stock."""
    symbol: str
    name: str
    current_price: float
    indicators: TechnicalIndicators
    trend: str  # 'bullish', 'bearish', 'neutral'
    strength: float  # 0-100 score
    signals: List[str]  # List of signals like "RSI Oversold", "MACD Bullish Cross"
    recommendation: str  # 'strong_buy', 'buy', 'hold', 'sell', 'strong_sell'
    
    def to_dict(self):
        return {
            'symbol': self.symbol,
            'name': self.name,
            'current_price': self.current_price,
            'indicators': self.indicators.to_dict(),
            'trend': self.trend,
            'strength': self.strength,
            'signals': self.signals,
            'recommendation': self.recommendation
        }

@dataclass
class TechnicalAgentInput:
    """Input schema for Technical Agent."""
    stocks: List[Dict[str, Any]]  # List of stocks from scouting agent
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TechnicalAgentInput':
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
class TechnicalAgentOutput:
    """Output schema for Technical Agent."""
    analyzed_stocks: List[Dict[str, Any]]
    total_analyzed: int
    bullish_count: int
    bearish_count: int
    neutral_count: int
    
    def to_dict(self):
        return asdict(self)
"""
Strategist Agent Schemas
Defines input and output contracts for the strategist agent.
"""

from dataclasses import dataclass, asdict
from typing import Optional, List, Dict, Any


@dataclass
class StrategistAgentInput:
    """Input schema for Strategist Agent."""
    technical_data: Dict[str, Any]  # Output from technical agent
    sentiment_data: Dict[str, Any]  # Output from sentiment agent
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'StrategistAgentInput':
        """Create from dictionary."""
        return cls(
            technical_data=data.get('technical', {}),
            sentiment_data=data.get('sentiment', {})
        )
    
    def validate(self) -> bool:
        """Validate input."""
        return (
            isinstance(self.technical_data, dict) and
            isinstance(self.sentiment_data, dict) and
            len(self.technical_data) > 0 and
            len(self.sentiment_data) > 0
        )


@dataclass
class TradingDecision:
    """Final trading decision for a stock."""
    symbol: str
    name: str
    action: str  # 'buy', 'hold', 'sell'
    confidence: float  # 0.0 to 1.0
    reasoning: str
    technical_score: float
    sentiment_score: float
    combined_score: float
    quantity: Optional[int] = None  # Number of shares to buy
    stop_loss: Optional[float] = None
    target_price: Optional[float] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class StrategistAgentOutput:
    """Output schema for Strategist Agent."""
    decisions: List[Dict[str, Any]]  # List of TradingDecision
    top_pick: Optional[Dict[str, Any]] = None  # Best stock to buy
    order_executed: bool = False
    order_details: Optional[Dict[str, Any]] = None
    execution_reason: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)



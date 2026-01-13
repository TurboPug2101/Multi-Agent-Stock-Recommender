"""
Scouting Agent Schemas
Defines input and output contracts for the scouting agent.
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from datetime import datetime
from logging import Logger, getLogger

logger = getLogger(__name__)

@dataclass
class StockScreeningResult:
    """Schema for individual stock screening result."""
    symbol: str
    name: str
    current_price: float
    atr_percentage: Optional[float]
    avg_volume: float
    recent_volume: float
    volume_ratio: float
    meets_criteria: bool
    criteria_details: List[str]
    score: Optional[float] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        result = asdict(self)
        # Handle Optional fields
        if result['atr_percentage'] is None:
            result['atr_percentage'] = None
        if result['score'] is None:
            result.pop('score', None)
        return result


@dataclass
class ScoutingAgentInput:
    """Input schema for scouting agent."""
    top_n: int = 10  # Number of stocks to shortlist
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ScoutingAgentInput':
        """Create from dictionary."""
        return cls(
            top_n=data.get('top_n', 10)
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'top_n': self.top_n
        }
    
    def validate(self) -> bool:
        """Validate input data."""
        if not isinstance(self.top_n, int):
            return False
        if self.top_n < 1 or self.top_n > 50:
            return False
        return True


@dataclass
class ScoutingAgentOutput:
    """Output schema for scouting agent."""
    shortlisted_stocks: List[StockScreeningResult]
    total_screened: int
    qualifying_count: int
    criteria: Dict[str, Any]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'shortlisted_stocks': [stock.to_dict() for stock in self.shortlisted_stocks],
            'total_screened': self.total_screened,
            'qualifying_count': self.qualifying_count,
            'criteria': self.criteria
        }


def get_scouting_input_schema() -> Dict[str, Any]:
    """Return input schema definition."""
    return {
        'type': 'object',
        'properties': {
            'top_n': {
                'type': 'integer',
                'description': 'Number of stocks to shortlist (1-50)',
                'minimum': 1,
                'maximum': 50,
                'default': 10
            }
        },
        'required': [],
        'additionalProperties': False
    }


def get_scouting_output_schema() -> Dict[str, Any]:
    """Return output schema definition."""
    return {
        'type': 'object',
        'properties': {
            'shortlisted_stocks': {
                'type': 'array',
                'items': {
                    'type': 'object',
                    'properties': {
                        'symbol': {'type': 'string'},
                        'name': {'type': 'string'},
                        'current_price': {'type': 'number'},
                        'atr_percentage': {'type': ['number', 'null']},
                        'avg_volume': {'type': 'number'},
                        'recent_volume': {'type': 'number'},
                        'volume_ratio': {'type': 'number'},
                        'meets_criteria': {'type': 'boolean'},
                        'criteria_details': {'type': 'array', 'items': {'type': 'string'}},
                        'score': {'type': ['number', 'null']}
                    },
                    'required': ['symbol', 'name', 'current_price', 'atr_percentage',
                                'avg_volume', 'recent_volume', 'volume_ratio',
                                'meets_criteria', 'criteria_details']
                }
            },
            'total_screened': {'type': 'integer'},
            'qualifying_count': {'type': 'integer'},
            'criteria': {
                'type': 'object',
                'properties': {
                    'atr_range': {'type': 'string'},
                    'volume_ratio_min': {'type': 'number'},
                    'min_avg_volume': {'type': 'number'}
                }
            }
        },
        'required': ['shortlisted_stocks', 'total_screened', 'qualifying_count', 'criteria']
    }

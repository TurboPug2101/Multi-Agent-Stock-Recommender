"""
Technical Agent
Performs technical analysis on stocks shortlisted by the scouting agent.
Conforms to BaseAgent contract.
"""

from typing import Dict, Any, Optional
import logging
from common.base_agent import BaseAgent
from .technical_schemas import TechnicalAgentInput, TechnicalAgentOutput
from .technical_tools import analyze_stock_technical
from agents.scouting.data_provider import StockDataProvider

logger = logging.getLogger(__name__)


class TechnicalAgent(BaseAgent):
    """
    Agent responsible for technical analysis of shortlisted stocks.
    Conforms to BaseAgent contract.
    """
    
    def __init__(self, data_provider: StockDataProvider = None):
        """
        Initialize the Technical Agent.
        
        Args:
            data_provider: Optional data provider instance
        """
        super().__init__(agent_name="technical_agent")
        # Import here to avoid circular dependency
        from agents.scouting.data_provider import YahooFinanceProvider, StockDataProvider
        self.data_provider: StockDataProvider = data_provider or YahooFinanceProvider()
    
    def validate_input(self, input_data: Dict[str, Any]) -> bool:
        """Validate input data."""
        try:
            technical_input = TechnicalAgentInput.from_dict(input_data)
            return technical_input.validate()
        except:
            return False
    
    def run(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Main execution method.
        Receives stocks from scouting agent and performs technical analysis.
        
        Args:
            input_data: Must contain 'stocks' key with list of stocks
        
        Returns:
            Dict with technical analysis results
        """
        logger.info("Starting technical agent execution")
        logger.debug(f"Received input data keys: {list(input_data.keys())}")
        logger.debug(f"Input data sample: {str(input_data)[:200]}...")
        
        # Parse and validate input
        technical_input = TechnicalAgentInput.from_dict(input_data)
        
        if not technical_input.validate():
            logger.error(f"Invalid input data. Input keys: {list(input_data.keys())}")
            logger.error(f"Stocks type: {type(technical_input.stocks)}, length: {len(technical_input.stocks) if isinstance(technical_input.stocks, list) else 'N/A'}")
            raise ValueError("Technical agent requires 'stocks' list in input")
        
        stocks = technical_input.stocks
        logger.info(f"Received {len(stocks)} stocks for technical analysis")
        
        if len(stocks) > 0:
            logger.debug(f"Sample stock structure: {stocks[0]}")
        
        # Analyze each stock
        analyzed_stocks = []
        for stock_data in stocks:
            symbol = stock_data.get('symbol')
            name = stock_data.get('name', symbol)
            current_price = stock_data.get('current_price')
            
            if not symbol or current_price is None:
                logger.warning(f"Skipping stock with missing data: {stock_data}")
                continue
            
            logger.info(f"Analyzing {symbol}...")
            result = analyze_stock_technical(symbol, name, current_price, self.data_provider)
            
            if result:
                analyzed_stocks.append(result.to_dict())
        
        logger.info(f"Successfully analyzed {len(analyzed_stocks)}/{len(stocks)} stocks")
        
        # Count trends
        bullish_count = len([s for s in analyzed_stocks if s['trend'] == 'bullish'])
        bearish_count = len([s for s in analyzed_stocks if s['trend'] == 'bearish'])
        neutral_count = len([s for s in analyzed_stocks if s['trend'] == 'neutral'])
        
        # Create output
        output = TechnicalAgentOutput(
            analyzed_stocks=analyzed_stocks,
            total_analyzed=len(analyzed_stocks),
            bullish_count=bullish_count,
            bearish_count=bearish_count,
            neutral_count=neutral_count
        )
        
        logger.info(f"Technical analysis complete: {bullish_count} bullish, {bearish_count} bearish, {neutral_count} neutral")
        
        return output.to_dict()


def create_agent(config: Dict[str, Any] = None) -> TechnicalAgent:
    """
    Factory function to create a TechnicalAgent instance.
    
    Args:
        config: Optional configuration dict with 'data_provider', etc.
    
    Returns:
        TechnicalAgent instance
    """
    logger.info(f"Creating TechnicalAgent with config: {config}")
    data_provider = config.get('data_provider') if config else None
    return TechnicalAgent(data_provider=data_provider)
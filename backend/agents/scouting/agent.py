"""
Scouting Agent
Screens Nifty 50 stocks based on liquidity, volume, and volatility (ATR) criteria
and shortlists top 10 stocks for further analysis by other agents.

Follows architecture principles:
- Inherits from BaseAgent (mandatory contract)
- Stateless and deterministic
- No side effects
- Strong input/output schemas
- Business logic decoupled from data provider
"""

from typing import Dict, Any
import logging
# Absolute import - assumes backend directory is on PYTHONPATH
from common.base_agent import BaseAgent

logger = logging.getLogger(__name__)
from .schemas import (
    ScoutingAgentInput,
    ScoutingAgentOutput,
    StockScreeningResult,
    get_scouting_input_schema,
    get_scouting_output_schema
)
from .tools import (
    get_nifty50_symbols,
    screen_stocks,
    shortlist_stocks
)
from .data_provider import StockDataProvider, YahooFinanceProvider


class ScoutingAgent(BaseAgent):
    """
    Agent responsible for screening and shortlisting stocks from Nifty 50.
    Conforms to BaseAgent contract.
    """
    
    def __init__(self, data_provider: StockDataProvider = None):
        """
        Initialize the Scouting Agent.
        
        Args:
            data_provider: Optional data provider instance (defaults to YahooFinanceProvider)
        """
        super().__init__(agent_name="scouting_agent")
        # Inject data provider dependency (business logic doesn't depend on specific provider)
        self.data_provider = data_provider or YahooFinanceProvider()
    
    def validate_input(self, input_data: Dict[str, Any]) -> bool:
        """
        Validate input data against schema.
        
        Args:
            input_data: Input data dictionary
        
        Returns:
            bool: True if valid, False otherwise
        """
        try:
            scouting_input = ScoutingAgentInput.from_dict(input_data)
            return scouting_input.validate()
        except (KeyError, TypeError, ValueError):
            return False
    
    def get_input_schema(self) -> Dict[str, Any]:
        """
        Return the input schema definition.
        
        Returns:
            Dict describing the expected input structure
        """
        return get_scouting_input_schema()
    
    def get_output_schema(self) -> Dict[str, Any]:
        """
        Return the output schema definition.
        
        Returns:
            Dict describing the output structure
        """
        return get_scouting_output_schema()
    
    def run(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Main execution method.
        Stateless, deterministic, no side effects.
        
        Args:
            input_data: Validated input data conforming to input schema
        
        Returns:
            Dict with output data conforming to output schema
        """
        logger.info("Starting scouting agent execution")
        
        # Parse input using schema
        scouting_input = ScoutingAgentInput.from_dict(input_data)
        logger.info(f"Scouting input - top_n: {scouting_input.top_n}")
        
        # Get Nifty 50 symbols
        logger.info("Fetching Nifty 50 stock symbols...")
        symbols = get_nifty50_symbols()
        logger.info(f"Found {len(symbols)} Nifty 50 stocks to screen")
        
        # Screen all stocks (pure business logic function)
        logger.info("Starting stock screening...")
        screening_results = screen_stocks(symbols, self.data_provider)
        logger.info(f"Screening completed. Successfully screened {len(screening_results)} stocks")
        
        # Count qualifying stocks
        qualifying_count = len([r for r in screening_results if r.meets_criteria])
        logger.info(f"Stocks meeting criteria: {qualifying_count}/{len(screening_results)}")
        
        # Shortlist top N stocks (pure business logic function)
        logger.info(f"Shortlisting top {scouting_input.top_n} stocks...")
        shortlisted = shortlist_stocks(screening_results, top_n=scouting_input.top_n)
        logger.info(f"Shortlisted {len(shortlisted)} stocks")
        
        # Create output using schema
        output = ScoutingAgentOutput(
            shortlisted_stocks=shortlisted,
            total_screened=len(screening_results),
            qualifying_count=qualifying_count,
            criteria={
                'atr_range': '2-5%',
                'volume_ratio_min': 0.8,
                'min_avg_volume': 100000
            }
        )
        
        logger.info("Scouting agent execution completed successfully")
        
        # Return as dictionary
        return output.to_dict()


def create_agent(config: Dict[str, Any] = None) -> ScoutingAgent:
    """
    Factory function to create a ScoutingAgent instance.
    
    Args:
        config: Optional configuration dict
    
    Returns:
        ScoutingAgent instance
    """
    # Data provider can be injected via config if needed
    data_provider = config.get('data_provider') if config else None
    return ScoutingAgent(data_provider=data_provider)


# For backward compatibility and direct execution
if __name__ == "__main__":
    agent = ScoutingAgent()
    result = agent.execute({'top_n': 10})
    
    print("\n" + "="*80)
    print("SCOUTING AGENT RESULTS")
    print("="*80)
    print(f"\nStatus: {result['status']}")
    print(f"Timestamp: {result['timestamp']}")
    
    if result['status'] == 'success' and result['data']:
        data = result['data']
        print(f"\nTotal Screened: {data['total_screened']}")
        print(f"Qualifying Stocks: {data['qualifying_count']}")
        print(f"\nShortlisted Stocks ({len(data['shortlisted_stocks'])}):")
        print("-"*80)
        
        for i, stock in enumerate(data['shortlisted_stocks'], 1):
            print(f"\n{i}. {stock['name']} ({stock['symbol']})")
            print(f"   Price: ₹{stock['current_price']:.2f}")
            print(f"   ATR: {stock['atr_percentage']:.2f}%" if stock['atr_percentage'] else "   ATR: N/A")
            print(f"   Avg Volume: {stock['avg_volume']:,.0f}")
            print(f"   Volume Ratio: {stock['volume_ratio']:.2f}")
            print(f"   Meets Criteria: {'Yes' if stock['meets_criteria'] else 'No'}")
            if stock.get('score'):
                print(f"   Score: {stock['score']:.2f}")
    else:
        print(f"\nError: {result.get('error', 'Unknown error')}")

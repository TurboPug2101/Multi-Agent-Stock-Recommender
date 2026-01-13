"""
Sentiment Agent
Analyzes news sentiment for stocks shortlisted by the scouting agent.
Uses Groq Qwen reasoning model for sentiment analysis.
Conforms to BaseAgent contract.
"""

from typing import Dict, Any, Optional
import logging
import os
from pathlib import Path
from dotenv import load_dotenv
from groq import Groq
from common.base_agent import BaseAgent

# Load environment variables from .env file
env_path = Path(__file__).parent.parent.parent / '.env'
load_dotenv(dotenv_path=env_path)
from .sentiment_schemas import (
    SentimentAgentInput,
    SentimentAgentOutput,
    get_sentiment_input_schema,
    get_sentiment_output_schema
)
from .sentiment_tools import analyze_sentiment_with_groq
from .news_provider import NewsDataProvider, NewsAPIProvider

logger = logging.getLogger(__name__)


class SentimentAgent(BaseAgent):
    """
    Agent responsible for sentiment analysis of shortlisted stocks.
    Conforms to BaseAgent contract.
    """
    
    def __init__(
        self,
        news_provider: Optional[NewsDataProvider] = None,
        groq_client: Optional[Groq] = None,
        groq_api_key: Optional[str] = None,
        groq_model_name: str = "qwen/qwen3-32b"
    ):
        """
        Initialize the Sentiment Agent.
        
        Args:
            news_provider: Optional news data provider instance (defaults to NewsAPIProvider)
            groq_client: Optional Groq client instance
            groq_api_key: Optional Groq API key (if not provided, uses GROQ_API_KEY env var)
            groq_model_name: Groq model name (default: "qwen/qwen3-32b")
        """
        super().__init__(agent_name="sentiment_agent")
        self.news_provider = news_provider or NewsAPIProvider()
        self.groq_model_name = groq_model_name
        
        # Initialize Groq client
        if groq_client:
            self.groq_client = groq_client
        else:
            api_key = groq_api_key or os.getenv('GROQ_API_KEY')
            if not api_key:
                logger.warning("GROQ_API_KEY not found. Sentiment analysis may fail.")
            self.groq_client = Groq(api_key=api_key) if api_key else None
    
    def validate_input(self, input_data: Dict[str, Any]) -> bool:
        """Validate input data."""
        try:
            sentiment_input = SentimentAgentInput.from_dict(input_data)
            return sentiment_input.validate()
        except Exception:
            return False
    
    def get_input_schema(self) -> Dict[str, Any]:
        """Return input schema."""
        return get_sentiment_input_schema()
    
    def get_output_schema(self) -> Dict[str, Any]:
        """Return output schema."""
        return get_sentiment_output_schema()
    
    def run(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Main execution method.
        Receives stocks from scouting agent and performs sentiment analysis.
        
        Args:
            input_data: Must contain 'stocks' key with list of stocks
        
        Returns:
            Dict with sentiment analysis results
        """
        logger.info("Starting sentiment agent execution")
        logger.debug(f"Received input data keys: {list(input_data.keys())}")
        
        if self.groq_client is None:
            logger.error("Groq client not initialized. Cannot perform sentiment analysis.")
            raise ValueError("Groq API key is required for sentiment analysis")
        
        # Parse and validate input
        sentiment_input = SentimentAgentInput.from_dict(input_data)
        logger.info("================================================")
        logger.info(f"Sentiment input: {sentiment_input}")
        logger.info("================================================")
        if not sentiment_input.validate():
            logger.error("Invalid input data")
            raise ValueError("Sentiment agent requires 'stocks' list in input")
        
        stocks = sentiment_input.stocks
        logger.info(f"Received {len(stocks)} stocks for sentiment analysis")
        
        if len(stocks) > 0:
            logger.debug(f"Sample stock structure: {stocks[0]}")
        
        # Analyze each stock
        analyzed_stocks = []
        for stock_data in stocks:
            symbol = stock_data.get('symbol')
            name = stock_data.get('name', symbol)
            
            if not symbol:
                logger.warning(f"Skipping stock with missing symbol: {stock_data}")
                continue
            
            logger.info(f"Analyzing sentiment for {symbol} ({name})...")
            
            # Fetch news articles (14 days)
            logger.debug(f"Fetching news for {symbol}...")
            news_articles = self.news_provider.fetch_news(symbol, name, days=14)
            logger.info(f"Found {len(news_articles)} news articles for {symbol}")
            
            if not news_articles:
                logger.warning(f"No news articles found for {symbol}, skipping sentiment analysis")
                continue
            
            # Analyze sentiment using Groq
            result = analyze_sentiment_with_groq(
                symbol=symbol,
                company_name=name,
                news_articles=news_articles,
                groq_client=self.groq_client,
                model_name=self.groq_model_name
            )
            
            if result:
                analyzed_stocks.append(result.to_dict())
            else:
                logger.warning(f"Failed to analyze sentiment for {symbol}")
        
        logger.info(f"Successfully analyzed {len(analyzed_stocks)}/{len(stocks)} stocks")
        
        # Count sentiments
        positive_count = len([
            s for s in analyzed_stocks 
            if s.get('overall_sentiment') in ['positive', 'very_positive']
        ])
        negative_count = len([
            s for s in analyzed_stocks 
            if s.get('overall_sentiment') in ['negative', 'very_negative']
        ])
        neutral_count = len([
            s for s in analyzed_stocks 
            if s.get('overall_sentiment') == 'neutral'
        ])
        
        # Create output
        output = SentimentAgentOutput(
            analyzed_stocks=analyzed_stocks,
            total_analyzed=len(analyzed_stocks),
            positive_count=positive_count,
            negative_count=negative_count,
            neutral_count=neutral_count
        )
        
        logger.info(f"Sentiment analysis complete: {positive_count} positive, {negative_count} negative, {neutral_count} neutral")
        
        return output.to_dict()


def create_agent(config: Dict[str, Any] = None) -> SentimentAgent:
    """
    Factory function to create a SentimentAgent instance.
    
    Args:
        config: Optional configuration dict with 'news_provider', 'groq_api_key', etc.
    
    Returns:
        SentimentAgent instance
    """
    news_provider = config.get('news_provider') if config else None
    groq_api_key = config.get('groq_api_key') if config else None
    groq_client = config.get('groq_client') if config else None
    
    logger.info(f"Creating SentimentAgent with config: {config}")
    return SentimentAgent(
        news_provider=news_provider,
        groq_client=groq_client,
        groq_api_key=groq_api_key
    )

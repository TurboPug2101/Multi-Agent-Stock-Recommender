"""
Sentiment Agent
Analyzes news sentiment for stocks shortlisted by the scouting agent.
Uses Groq Qwen reasoning model for sentiment analysis.
Agentic implementation with autonomous tool calling and adaptive data collection.
Conforms to BaseAgent contract.
"""

from typing import Dict, Any, Optional, List
import logging
import os
import json
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
    NewsArticle
)
from .sentiment_tools import analyze_sentiment_with_groq
from .agent_tools import ToolRegistry, Tool
from .social_media_tools import (
    fetch_news,
    fetch_twitter_mentions,
    fetch_reddit_mentions,
    fetch_gnews_articles,
    SocialMention
)
from common.cache import get_cache

logger = logging.getLogger(__name__)


class SentimentAgent(BaseAgent):
    """
    Agent responsible for sentiment analysis of shortlisted stocks.
    Conforms to BaseAgent contract.
    """
    
    def __init__(
        self,
        groq_client: Optional[Groq] = None,
        groq_api_key: Optional[str] = None,
        groq_model_name: str = "qwen/qwen3-32b",
        min_news_threshold: int = 5,
        max_expansion_months: int = 6
    ):
        """
        Initialize the Sentiment Agent.
        
        Args:
            groq_client: Optional Groq client instance
            groq_api_key: Optional Groq API key (if not provided, uses GROQ_API_KEY env var)
            groq_model_name: Groq model name (default: "qwen/qwen3-32b")
            min_news_threshold: Minimum number of articles needed for analysis (default: 5)
            max_expansion_months: Maximum months to expand search (default: 6)
        """
        super().__init__(agent_name="sentiment_agent")
        self.groq_model_name = groq_model_name
        self.min_news_threshold = min_news_threshold
        self.max_expansion_months = max_expansion_months
        
        # Initialize Groq client
        if groq_client:
            self.groq_client = groq_client
        else:
            api_key = groq_api_key or os.getenv('GROQ_API_KEY')
            if not api_key:
                logger.warning("GROQ_API_KEY not found. Sentiment analysis may fail.")
            self.groq_client = Groq(api_key=api_key) if api_key else None
        
        # Initialize tool registry
        self.tool_registry = self._initialize_tool_registry()
    
    def validate_input(self, input_data: Dict[str, Any]) -> bool:
        """Validate input data."""
        try:
            sentiment_input = SentimentAgentInput.from_dict(input_data)
            return sentiment_input.validate()
        except Exception:
            return False
    
    def _initialize_tool_registry(self) -> ToolRegistry:
        """Initialize and register all available tools."""
        from .agent_tools import ToolRegistry, Tool
        
        registry = ToolRegistry()
        
        # Common parameter schema
        common_params = {
            "type": "object",
            "properties": {
                "symbol": {"type": "string", "description": "Stock symbol"},
                "company_name": {"type": "string", "description": "Company name"},
                "days": {"type": "integer", "description": "Number of days to look back"},
                "max_results": {"type": "integer", "description": "Maximum results"}
            },
            "required": ["symbol", "company_name"]
        }
        
        # Register tools
        registry.register(Tool(
            name="fetch_news",
            description="Fetch news from primary provider. Use first. Can expand days (2→90→180).",
            parameters=common_params,
            function=fetch_news
        ))
        
        registry.register(Tool(
            name="fetch_gnews",
            description="Fetch news from GNews API (alternative source). Use when primary has low volume.",
            parameters=common_params,
            function=fetch_gnews_articles
        ))
        
        registry.register(Tool(
            name="fetch_twitter_mentions",
            description="Fetch Twitter/X mentions. Use for social sentiment when news is low.",
            parameters=common_params,
            function=fetch_twitter_mentions
        ))
        
        registry.register(Tool(
            name="fetch_reddit_mentions",
            description="Fetch Reddit mentions from r/stocks, r/investing. Use for social sentiment.",
            parameters=common_params,
            function=fetch_reddit_mentions
        ))
        
        logger.info(f"Initialized {len(registry.tools)} tools")
        return registry
    
    def _reason_about_data_sufficiency(
        self,
        symbol: str,
        company_name: str,
        news_count: int,
        current_days: int
    ) -> Dict[str, Any]:
        """
        Agent reasons about whether it has sufficient data for sentiment analysis.
        
        Returns:
            Dict with 'sufficient', 'reasoning', 'plan' keys
        """
        logger.info(f"Agent reasoning about data sufficiency for {symbol} ({news_count} articles)")
        
        # Simplified prompt
        prompt = f"""
You are a senior financial sentiment analyst working on a risk-sensitive trading system.

Your job is NOT to be optimistic.
Your job is to PREVENT decisions based on weak, biased, or insufficient data.

Context:
- Company: {company_name} ({symbol})
- Articles available: {news_count}
- Time coverage: last {current_days} days
- Minimum threshold: {self.min_news_threshold} articles

IMPORTANT PRINCIPLES (you MUST follow these):

1. Financial sentiment analysis requires BROAD and DIVERSE data.
2. Small sample sizes are EXTREMELY risky and often misleading.
3. If there are fewer than 2× the minimum threshold, you should generally assume data is INSUFFICIENT.
4. If articles are concentrated in a short time window, assume EVENT BIAS.
5. If data comes from a single source type, assume SOURCE BIAS.
6. When in doubt, ALWAYS choose to gather more data.

You should only return "sufficient = true" if:
- Article count is comfortably above the threshold
- Coverage spans multiple days or weeks
- The sample size would reasonably capture both positive and negative viewpoints

Otherwise, return "sufficient = false".

Available tools you can plan to use:
1. fetch_news
   - Purpose: Fetches mainstream financial and business news articles.
   - Signal quality: HIGH
   - Best for: Regulatory events, earnings, corporate actions, macro developments.
   - Strengths: Structured reporting, lower noise, higher reliability.
   - Weaknesses: Slower to react, limited article volume for short windows.
   - Use when: Article count is low or coverage window is too short.
   - Preferred expansion path.

2. fetch_gnews
   - Purpose: Expands coverage using Google News–aggregated mainstream sources.
   - Signal quality: MEDIUM–HIGH
   - Best for: Broadening source diversity and catching missed coverage.
   - Strengths: Wider publisher reach, good regional coverage.
   - Weaknesses: Some articles may be summaries or duplicates.
   - Use when: fetch_news returns few articles or limited source diversity.

3. fetch_reddit_mentions
   - Purpose: Collects discussion-based social sentiment from investor communities.
   - Signal quality: LOW–MEDIUM
   - Best for: Retail investor sentiment, rumors, crowd psychology.
   - Strengths: Early signals, contrarian indicators.
   - Weaknesses: High noise, bias, speculation, emotional language.
   - Use when: Mainstream news is insufficient or when sentiment needs validation.
   - Must NEVER be used as a sole source.

4. fetch_twitter_mentions
   - Purpose: Captures short-term, real-time reactions and breaking chatter.
   - Signal quality: LOW
   - Best for: Event detection and immediate reaction tracking.
   - Strengths: Fastest signal.
   - Weaknesses: Extremely noisy, bot-driven, unreliable without confirmation.
   - Use only as a supplement and with caution.

Respond STRICTLY in JSON with this structure:

{{
  "sufficient": true | false,
  "reasoning": "Concise explanation focused on data adequacy, bias risk, and coverage quality",
  "plan": {{
    "action": "proceed | expand_search | use_alternative | check_social_media | combine_sources",
    "tools_to_call": ["tool_name_1", "tool_name_2"],
    "parameters": {{
      "days": 90,
      "max_results": 50
    }}
  }}
}}"""

        try:
            completion = self.groq_client.chat.completions.create(
                model=self.groq_model_name,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.5,
                response_format={"type": "json_object"}
            )
            
            decision = json.loads(completion.choices[0].message.content)
            logger.info(f"Agent decision: sufficient={decision.get('sufficient')}, action={decision.get('plan', {}).get('action')}")
            logger.info("================================================")
            logger.info(f"Agent decision: {decision}")
            logger.info("================================================")
            return decision
            
        except Exception as e:
            logger.error(f"Error in agent reasoning: {e}", exc_info=True)
            # Simple fallback
            sufficient = news_count >= self.min_news_threshold
            return {
                "sufficient": sufficient,
                "reasoning": f"{news_count} articles {'meets' if sufficient else 'below'} threshold",
                "plan": {
                    "action": "proceed" if sufficient else "expand_search",
                    "tools_to_call": ["fetch_news"] if not sufficient else [],
                    "parameters": {"days": min(current_days * 3, 180)} if not sufficient else {}
                }
            }
    
    def _execute_plan(
        self,
        symbol: str,
        company_name: str,
        plan: Dict[str, Any]
    ) -> List[NewsArticle]:
        """
        Execute the agent's plan by calling tools.
        
        Returns:
            Combined list of NewsArticle objects from all sources
        """
        logger.info(f"Executing plan: {plan.get('action')}")
        
        all_articles: List[NewsArticle] = []
        tools_to_call = plan.get("tools_to_call", [])
        parameters = plan.get("parameters", {})
        
        for tool_name in tools_to_call:
            try:
                # Prepare tool arguments
                tool_params = {
                    "symbol": symbol,
                    "company_name": company_name,
                    **parameters
                }
                
                # Call tool
                result = self.tool_registry.call_tool(tool_name, **tool_params)
                logger.info("================================================")
                logger.info(f" result: {result}")
                logger.info("================================================")
                
                # Convert results to NewsArticle format
                if isinstance(result, list):
                    for item in result:
                        if isinstance(item, NewsArticle):
                            all_articles.append(item)
                        elif isinstance(item, SocialMention):
                            all_articles.append(item.to_news_article())
                
            except Exception as e:
                logger.error(f"Error executing tool {tool_name}: {e}", exc_info=True)
                continue
        
        return all_articles
    
    def _collect_data_agentically(
        self,
        symbol: str,
        company_name: str,
        initial_days: int = 2
    ) -> List[NewsArticle]:
        """
        Agentic data collection: Agent reasons about data needs and collects accordingly.
        
        Returns:
            List of NewsArticle objects from all sources
        """
        logger.info(f"Starting agentic data collection for {symbol}")
        
        all_articles: List[NewsArticle] = []
        current_days = initial_days
        max_iterations = 3
        
        # Initial fetch
        articles = self.tool_registry.call_tool(
            "fetch_news",
            symbol=symbol,
            company_name=company_name,
            days=current_days
        )
        all_articles.extend(articles)
        
        # Agentic loop: reason and collect until sufficient
        for iteration in range(1, max_iterations + 1):
            # Agent reasons about sufficiency
            decision = self._reason_about_data_sufficiency(
                symbol, company_name, len(all_articles), current_days
            )
            
            if decision.get("sufficient", False) or decision.get("plan", {}).get("action") == "proceed":
                break
            
            # Execute plan
            plan = decision.get("plan", {})
            logger.info("================================================")
            logger.info(f"Plan: {plan}")
            logger.info("================================================")
            additional = self._execute_plan(symbol, company_name, plan)
            all_articles.extend(additional)
            
            # Update days if expanded
            if "days" in plan.get("parameters", {}):
                current_days = plan["parameters"]["days"]
        
        # Remove duplicates
        seen = set()
        unique = []
        for article in all_articles:
            key = article.title.lower().strip()
            if key not in seen:
                seen.add(key)
                unique.append(article)
        
        logger.info(f"Collected {len(unique)} unique articles/mentions")
        return unique
    
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
        
        # Check cache (valid for 3 hours)
        cache = get_cache()
        # Create cache key from stock symbols (sorted for consistency)
        stock_symbols = sorted([s.get('symbol', '') for s in stocks if s.get('symbol')])
        cache_key = cache.generate_key('sentiment', stocks=','.join(stock_symbols))
        
        cached_result = cache.get(cache_key)
        if cached_result is not None:
            logger.info(f"Using cached sentiment result (valid for 3 hours)")
            return cached_result
        
        logger.info("Cache miss - computing sentiment analysis")
        
        # Analyze each stock
        analyzed_stocks = []
        for stock_data in stocks:
            symbol = stock_data.get('symbol')
            name = stock_data.get('name', symbol)
            
            if not symbol:
                logger.warning(f"Skipping stock with missing symbol: {stock_data}")
                continue
            
            logger.info(f"Analyzing sentiment for {symbol} ({name})...")
            
            # Agentic data collection: Agent reasons and collects data autonomously
            logger.info(f"Agent starting autonomous data collection for {symbol}...")
            news_articles = self._collect_data_agentically(symbol, name, initial_days=2)
            logger.info(f"Agent collected {len(news_articles)} articles/mentions for {symbol}")
            
            if not news_articles:
                logger.warning(f"No articles/mentions found for {symbol} after agentic collection, skipping sentiment analysis")
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
        
        # Cache the result (valid for 3 hours)
        output_dict = output.to_dict()
        cache.set(cache_key, output_dict)
        logger.info("Cached sentiment result for 3 hours")
        
        return output_dict


def create_agent(config: Dict[str, Any] = None) -> SentimentAgent:
    """
    Factory function to create a SentimentAgent instance.
    
    Args:
        config: Optional configuration dict with 'groq_api_key', etc.
    
    Returns:
        SentimentAgent instance
    """
    groq_api_key = config.get('groq_api_key') if config else None
    groq_client = config.get('groq_client') if config else None
    
    return SentimentAgent(
        groq_client=groq_client,
        groq_api_key=groq_api_key
    )

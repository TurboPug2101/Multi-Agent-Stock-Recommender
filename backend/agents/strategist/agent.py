"""
Strategist Agent
Makes final trading decisions by combining technical and sentiment analysis.
Can execute buy orders via Kite API if confidence is high.
"""

from typing import Dict, Any, Optional, List
import logging
import os
import json
from pathlib import Path
from dotenv import load_dotenv
from groq import Groq
from common.base_agent import BaseAgent

# Load environment variables
env_path = Path(__file__).parent.parent.parent / '.env'
load_dotenv(dotenv_path=env_path)

from .schemas import (
    StrategistAgentInput,
    StrategistAgentOutput,
    TradingDecision
)
from .kite_client import KiteClient

logger = logging.getLogger(__name__)


class StrategistAgent(BaseAgent):
    """
    Agent responsible for making final trading decisions.
    Combines technical and sentiment analysis to decide on buy/sell/hold.
    Can execute orders via Kite API if confidence is high.
    """
    
    def __init__(
        self,
        groq_client: Optional[Groq] = None,
        groq_api_key: Optional[str] = None,
        groq_model_name: str = "qwen/qwen3-32b",
        min_confidence_threshold: float = 0.75,
        paper_trading: bool = True,
        max_position_size: float = 0.1  # Max 10% of portfolio per trade
    ):
        """
        Initialize the Strategist Agent.
        
        Args:
            groq_client: Optional Groq client instance
            groq_api_key: Optional Groq API key
            groq_model_name: Groq model name
            min_confidence_threshold: Minimum confidence to execute order (0.0-1.0)
            paper_trading: If True, simulate orders without real execution
            max_position_size: Maximum position size as fraction of portfolio (default: 0.1 = 10%)
        """
        super().__init__(agent_name="strategist_agent")
        self.groq_model_name = groq_model_name
        self.min_confidence_threshold = min_confidence_threshold
        self.paper_trading = paper_trading
        self.max_position_size = max_position_size
        
        # Initialize Groq client
        if groq_client:
            self.groq_client = groq_client
        else:
            api_key = groq_api_key or os.getenv('GROQ_API_KEY')
            if not api_key:
                logger.warning("GROQ_API_KEY not found. Strategist reasoning may fail.")
            self.groq_client = Groq(api_key=api_key) if api_key else None
        
        # Initialize Kite client
        try:
            self.kite_client = KiteClient(paper_trading=paper_trading)
        except Exception as e:
            logger.warning(f"Kite client initialization failed: {e}. Order execution will be disabled.")
            self.kite_client = None
    
    def validate_input(self, input_data: Dict[str, Any]) -> bool:
        """Validate input data."""
        try:
            strategist_input = StrategistAgentInput.from_dict(input_data)
            return strategist_input.validate()
        except Exception:
            return False
    
    def _make_trading_decisions(
        self,
        technical_data: Dict[str, Any],
        sentiment_data: Dict[str, Any]
    ) -> List[TradingDecision]:
        """
        Use Groq to make trading decisions by combining technical and sentiment analysis.
        
        Returns:
            List of TradingDecision objects
        """
        logger.info("Strategist agent making trading decisions...")
        
        # Extract analyzed stocks from both agents
        technical_stocks = {s['symbol']: s for s in technical_data.get('analyzed_stocks', [])}
        sentiment_stocks = {s['symbol']: s for s in sentiment_data.get('analyzed_stocks', [])}
        
        # Combine data for each stock
        combined_stocks = []
        all_symbols = set(technical_stocks.keys()) | set(sentiment_stocks.keys())
        
        for symbol in all_symbols:
            tech = technical_stocks.get(symbol, {})
            sent = sentiment_stocks.get(symbol, {})
            
            combined_stocks.append({
                'symbol': symbol,
                'name': tech.get('name') or sent.get('name') or symbol,
                'current_price': tech.get('current_price', 0),
                'technical': {
                    'trend': tech.get('trend', 'neutral'),
                    'strength': tech.get('strength', 0),
                    'recommendation': tech.get('recommendation', 'hold'),
                    'signals': tech.get('signals', [])
                },
                'sentiment': {
                    'overall_sentiment': sent.get('overall_sentiment', 'neutral'),
                    'sentiment_score': sent.get('sentiment_score', 0),
                    'confidence': sent.get('confidence', 0),
                    'recommendation': sent.get('recommendation', 'hold')
                }
            })
        logger.info("Combined %d stocks", len(combined_stocks))
        logger.info("Combined stocks payload: %s", json.dumps(combined_stocks, indent=2))
        logger.info("================================================")
        if not combined_stocks:
            logger.warning("No stocks to analyze")
            return []
        
        # Create prompt for Groq
        prompt = f"""You are a senior trading strategist making buy/sell/hold decisions for a swing trading system.

Your task: Analyze each stock and make a final trading decision by combining technical and sentiment analysis.

IMPORTANT PRINCIPLES:
1. Only recommend BUY if BOTH technical and sentiment are strongly positive
2. Technical analysis is more reliable for entry timing
3. Sentiment analysis helps validate the decision
4. Be conservative - only high-confidence trades
5. Consider risk-reward ratio 1:2

Stocks to analyze:
{json.dumps(combined_stocks, indent=2)}

For each stock, provide:
1. Action: 'buy', 'hold', or 'sell'
2. Confidence: 0.0 to 1.0 (only recommend buy if > {self.min_confidence_threshold})
3. Reasoning: Brief explanation
4. Combined score: 0-100 based on technical + sentiment
5. Quantity: Number of shares (if buying, suggest based on risk management)
6. Stop loss: Suggested stop loss price (if buying)
7. Target price: Suggested target price (if buying)

Respond in JSON format:
{{
    "decisions": [
        {{
            "symbol": "RELIANCE.NS",
            "name": "Reliance Industries",
            "action": "buy",
            "confidence": 0.85,
            "reasoning": "Strong bullish technical pattern with positive sentiment",
            "technical_score": 75,
            "sentiment_score": 0.7,
            "combined_score": 72.5,
            "quantity": 10,
            "stop_loss": 2400,
            "target_price": 2600
        }}
    ]
}}"""

        try:
            completion = self.groq_client.chat.completions.create(
                model=self.groq_model_name,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                response_format={"type": "json_object"}
            )
            
            response_text = completion.choices[0].message.content
            logger.info("================================================")
            logger.info(f"response_text: {response_text}")
            logger.info(f"Strategist reasoning response received ")
            logger.info("================================================")
            
            # Parse response
            data = json.loads(response_text)
            decisions_data = data.get('decisions', [])
            
            decisions = []
            for dec_data in decisions_data:
                decision = TradingDecision(
                    symbol=dec_data.get('symbol', ''),
                    name=dec_data.get('name', ''),
                    action=dec_data.get('action', 'hold'),
                    confidence=float(dec_data.get('confidence', 0)),
                    reasoning=dec_data.get('reasoning', ''),
                    technical_score=float(dec_data.get('technical_score', 0)),
                    sentiment_score=float(dec_data.get('sentiment_score', 0)),
                    combined_score=float(dec_data.get('combined_score', 0)),
                    quantity=dec_data.get('quantity'),
                    stop_loss=dec_data.get('stop_loss'),
                    target_price=dec_data.get('target_price')
                )
                decisions.append(decision)
            
            logger.info(f"Made {len(decisions)} trading decisions")
            return decisions
            
        except Exception as e:
            logger.error(f"Error making trading decisions: {e}", exc_info=True)
            return []
    
    def _execute_buy_order(self, decision: TradingDecision) -> Dict[str, Any]:
        """
        Execute buy order if confidence is high enough.
        
        Returns:
            Order execution details
        """
        if not self.kite_client:
            return {
                "status": "error",
                "error": "Kite client not available"
            }
        
        if decision.confidence < self.min_confidence_threshold:
            return {
                "status": "skipped",
                "reason": f"Confidence {decision.confidence:.2f} below threshold {self.min_confidence_threshold}"
            }
        
        if decision.action != 'buy':
            return {
                "status": "skipped",
                "reason": f"Action is '{decision.action}', not 'buy'"
            }
        
        if not decision.quantity or decision.quantity <= 0:
            return {
                "status": "error",
                "error": "Invalid quantity"
            }
        
        logger.info(f"Executing BUY order for {decision.symbol}: {decision.quantity} shares (confidence: {decision.confidence:.2f})")
        
        # Execute order
        order_result = self.kite_client.place_order(
            symbol=decision.symbol,
            quantity=decision.quantity,
            order_type="MARKET",
            transaction_type="BUY"
        )
        
        return order_result
    
    def run(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Main execution method.
        Combines technical and sentiment analysis to make trading decisions.
        Executes buy order if confidence is high.
        
        Args:
            input_data: Must contain 'technical' and 'sentiment' keys
        
        Returns:
            Dict with trading decisions and execution results
        """
        logger.info("Starting strategist agent execution")
        
        if self.groq_client is None:
            logger.error("Groq client not initialized")
            raise ValueError("Groq API key is required for strategist agent")
        
        # Parse and validate input
        strategist_input = StrategistAgentInput.from_dict(input_data)
        if not strategist_input.validate():
            raise ValueError("Strategist agent requires 'technical' and 'sentiment' data")
        
        # Make trading decisions
        decisions = self._make_trading_decisions(
            strategist_input.technical_data,
            strategist_input.sentiment_data
        )
        
        if not decisions:
            logger.warning("No trading decisions made")
            return StrategistAgentOutput(
                decisions=[],
                order_executed=False
            ).to_dict()
        
        # Find top pick (highest confidence buy)
        buy_decisions = [d for d in decisions if d.action == 'buy' and d.confidence >= self.min_confidence_threshold]
        top_pick = None
        order_executed = False
        order_details = None
        execution_reason = None
        
        if buy_decisions:
            # Sort by confidence and combined score
            buy_decisions.sort(key=lambda x: (x.confidence, x.combined_score), reverse=True)
            top_pick = buy_decisions[0]
            
            logger.info(f"Top pick: {top_pick.symbol} ({top_pick.name}) - Confidence: {top_pick.confidence:.2f}")
            
            # Execute order for top pick
            order_result = self._execute_buy_order(top_pick)
            
            if order_result.get('status') == 'success':
                order_executed = True
                order_details = order_result
                execution_reason = f"High confidence ({top_pick.confidence:.2f}) buy signal for {top_pick.symbol}"
                logger.info(f"✓ Order executed: {order_result.get('order_id')}")
            else:
                execution_reason = f"Order not executed: {order_result.get('reason') or order_result.get('error')}"
                logger.info(f"Order not executed: {execution_reason}")
        
        # Create output
        output = StrategistAgentOutput(
            decisions=[d.to_dict() for d in decisions],
            top_pick=top_pick.to_dict() if top_pick else None,
            order_executed=order_executed,
            order_details=order_details,
            execution_reason=execution_reason
        )
        
        logger.info(f"Strategist execution complete. Decisions: {len(decisions)}, Order executed: {order_executed}")
        
        return output.to_dict()


def create_agent(config: Dict[str, Any] = None) -> StrategistAgent:
    """
    Factory function to create a StrategistAgent instance.
    
    Args:
        config: Optional configuration dict
    
    Returns:
        StrategistAgent instance
    """
    groq_api_key = config.get('groq_api_key') if config else None
    groq_client = config.get('groq_client') if config else None
    paper_trading = config.get('paper_trading', True) if config else True
    min_confidence = config.get('min_confidence_threshold', 0.75) if config else 0.75
    
    return StrategistAgent(
        groq_client=groq_client,
        groq_api_key=groq_api_key,
        paper_trading=paper_trading,
        min_confidence_threshold=min_confidence
    )

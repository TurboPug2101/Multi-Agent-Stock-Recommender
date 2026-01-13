"""
Zerodha Kite API Client
Handles order execution via Zerodha Kite API.
"""

import os
import logging
from typing import Dict, Any, Optional
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
env_path = Path(__file__).parent.parent.parent / '.env'
load_dotenv(dotenv_path=env_path)

logger = logging.getLogger(__name__)

try:
    from kiteconnect import KiteConnect
    KITE_AVAILABLE = True
except ImportError:
    KITE_AVAILABLE = False
    logger.warning("kiteconnect not installed. Install with: pip install kiteconnect")


class KiteClient:
    """Client for Zerodha Kite API."""
    
    def __init__(self, api_key: Optional[str] = None, access_token: Optional[str] = None, paper_trading: bool = True):
        """
        Initialize Kite client.
        
        Args:
            api_key: Kite API key
            access_token: Kite access token
            paper_trading: If True, simulate orders without real execution
        """
        self.paper_trading = paper_trading
        self.api_key = api_key or os.getenv('KITE_API_KEY')
        self.access_token = access_token or os.getenv('KITE_ACCESS_TOKEN')
        
        if not self.paper_trading:
            if not KITE_AVAILABLE:
                raise ImportError("kiteconnect package required for real trading")
            if not self.api_key or not self.access_token:
                raise ValueError("KITE_API_KEY and KITE_ACCESS_TOKEN required for real trading")
            
            self.kite = KiteConnect(api_key=self.api_key)
            self.kite.set_access_token(self.access_token)
            logger.info("Kite client initialized for REAL trading")
        else:
            logger.info("Kite client initialized for PAPER trading (simulation)")
    
    def get_instrument_token(self, symbol: str) -> Optional[str]:
        """
        Get instrument token for a symbol.
        For NSE stocks, format is usually: NSE:SYMBOL
        """
        # For paper trading, return mock token
        if self.paper_trading:
            return f"PAPER:{symbol}"
        
        try:
            # Search for instrument
            instruments = self.kite.instruments("NSE")
            for instrument in instruments:
                if instrument['tradingsymbol'] == symbol.replace('.NS', ''):
                    return f"NSE:{instrument['instrument_token']}"
            logger.warning(f"Instrument not found for {symbol}")
            return None
        except Exception as e:
            logger.error(f"Error getting instrument token: {e}")
            return None
    
    def place_order(
        self,
        symbol: str,
        quantity: int,
        order_type: str = "MARKET",
        transaction_type: str = "BUY",
        price: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Place an order.
        
        Args:
            symbol: Stock symbol (e.g., "RELIANCE.NS")
            quantity: Number of shares
            order_type: "MARKET" or "LIMIT"
            transaction_type: "BUY" or "SELL"
            price: Price for LIMIT orders
        
        Returns:
            Order details
        """
        if self.paper_trading:
            return self._place_paper_order(symbol, quantity, order_type, transaction_type, price)
        
        try:
            # Get instrument token
            instrument_token = self.get_instrument_token(symbol)
            if not instrument_token:
                return {
                    "status": "error",
                    "error": "Instrument token not found"
                }
            
            # Place order
            order_id = self.kite.place_order(
                variety=self.kite.VARIETY_REGULAR,
                exchange="NSE",
                tradingsymbol=symbol.replace('.NS', ''),
                transaction_type=self.kite.TRANSACTION_TYPE_BUY if transaction_type == "BUY" else self.kite.TRANSACTION_TYPE_SELL,
                quantity=quantity,
                order_type=self.kite.ORDER_TYPE_MARKET if order_type == "MARKET" else self.kite.ORDER_TYPE_LIMIT,
                product=self.kite.PRODUCT_MIS,  # MIS (Intraday)
                price=price if order_type == "LIMIT" else None
            )
            
            logger.info(f"Order placed: {order_id} for {symbol}, quantity: {quantity}")
            
            return {
                "status": "success",
                "order_id": order_id,
                "symbol": symbol,
                "quantity": quantity,
                "order_type": order_type,
                "transaction_type": transaction_type
            }
            
        except Exception as e:
            logger.error(f"Error placing order: {e}", exc_info=True)
            return {
                "status": "error",
                "error": str(e)
            }
    
    def _place_paper_order(
        self,
        symbol: str,
        quantity: int,
        order_type: str,
        transaction_type: str,
        price: Optional[float]
    ) -> Dict[str, Any]:
        """Simulate order execution for paper trading."""
        logger.info(f"[PAPER TRADING] Simulating {transaction_type} order: {symbol}, quantity: {quantity}, type: {order_type}")
        
        # In real implementation, you'd track this in a database
        return {
            "status": "success",
            "order_id": f"PAPER_{symbol}_{quantity}",
            "symbol": symbol,
            "quantity": quantity,
            "order_type": order_type,
            "transaction_type": transaction_type,
            "paper_trading": True,
            "message": "Order simulated (paper trading mode)"
        }
    
    def get_quote(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get current quote for a symbol."""
        if self.paper_trading:
            # Return mock quote
            return {
                "last_price": 0.0,
                "paper_trading": True
            }
        
        try:
            tradingsymbol = symbol.replace('.NS', '')
            quote = self.kite.quote(f"NSE:{tradingsymbol}")
            return quote.get(f"NSE:{tradingsymbol}", {})
        except Exception as e:
            logger.error(f"Error getting quote: {e}")
            return None

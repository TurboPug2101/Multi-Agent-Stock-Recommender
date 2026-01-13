"""
Data Provider Interface
Abstracts data provider implementation to decouple business logic from data sources.
"""

from abc import ABC, abstractmethod
from typing import Optional, Dict, Any
import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime, timedelta
from logging import Logger, getLogger

logger = getLogger(__name__)

class StockDataProvider(ABC):
    """Abstract interface for stock data providers."""
    
    @abstractmethod
    def fetch_historical_data(self, symbol: str, period: str = "1mo") -> Optional[pd.DataFrame]:
        """
        Fetch historical stock data.
        
        Args:
            symbol: Stock symbol
            period: Data period (1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, max)
        
        Returns:
            DataFrame with columns: Open, High, Low, Close, Volume, or None if fails
        """
        pass
    
    @abstractmethod
    def fetch_stock_info(self, symbol: str) -> Dict[str, Any]:
        """
        Fetch stock information.
        
        Args:
            symbol: Stock symbol
        
        Returns:
            Dict with stock information (e.g., name, sector, etc.)
        """
        pass


class YahooFinanceProvider(StockDataProvider):
    """Yahoo Finance implementation of StockDataProvider."""
    
    def fetch_historical_data(self, symbol: str, period: str = "1mo") -> Optional[pd.DataFrame]:
        """
        Fetch historical stock data from Yahoo Finance.
        
        Args:
            symbol: Stock symbol in Yahoo Finance format (e.g., "RELIANCE.NS")
            period: Data period
        
        Returns:
            DataFrame with stock data or None if fetch fails
        """
        # # Return static dummy data for RELIANCE.NS
        if symbol == "RELIANCE.NS":
            logger.info(f"Returning DUMMY data for {symbol}")
            # Generate ~66 days of trading data (3 months)
            dates = []
            end_date = datetime.now()
            current_date = end_date - timedelta(days=100)  # Start earlier to account for weekends
            while len(dates) < 66:
                if current_date.weekday() < 5:  # Monday = 0, Friday = 4
                    dates.append(current_date)
                current_date += timedelta(days=1)
            dates = dates[-66:]  # Take last 66 days
            
            # Generate realistic price data for RELIANCE (base price ~2450)
            base_price = 2450.0
            prices = []
            current = base_price
            np.random.seed(42)  # For reproducibility
            
            for _ in range(66):
                change = np.random.normal(0.001, 0.025)  # Small upward drift with 2.5% volatility
                current = current * (1 + change)
                prices.append(current)
            
            # Generate OHLC data
            data = []
            for i, (date, close_price) in enumerate(zip(dates, prices)):
                daily_range = close_price * 0.025 * np.random.uniform(0.5, 1.5)
                high = close_price + daily_range * np.random.uniform(0.3, 0.7)
                low = close_price - daily_range * np.random.uniform(0.3, 0.7)
                open_price = close_price + np.random.uniform(-daily_range * 0.3, daily_range * 0.3)
                
                high = max(high, open_price, close_price)
                low = min(low, open_price, close_price)
                
                price_change_pct = abs((close_price - open_price) / open_price)
                base_volume = 1000000
                volume = int(base_volume * (1 + price_change_pct * 5) * np.random.uniform(0.7, 1.3))
                
                data.append({
                    'Open': round(open_price, 2),
                    'High': round(high, 2),
                    'Low': round(low, 2),
                    'Close': round(close_price, 2),
                    'Volume': volume
                })
            
            df = pd.DataFrame(data, index=pd.DatetimeIndex(dates))
            logger.info(f"Generated {len(df)} rows of dummy data for {symbol}")
            logger.info(f"df: {df}")
            return df
        
        # True implementation (commented out for now)
        # try:
        #     ticker = yf.Ticker(symbol)
        #     data = ticker.history(period=period)
        #     logger.info(f"Fetched Yahoo data for {symbol}")
        #     logger.debug(f"Rows: {len(data)}")
        #     logger.debug(f"Head:\n{data.head()}")
        #     if data is None or data.empty:
        #         logger.warning(f"No Yahoo data for {symbol}")
        #         return None
        #     else:
        #         return data
        # except Exception:
        #     return None
        
        # For other symbols, return None (or you can uncomment above for real API)
        logger.warning(f"No dummy data available for {symbol}, returning None")
        return None
    
    def fetch_stock_info(self, symbol: str) -> Dict[str, Any]:
        """
        Fetch stock information from Yahoo Finance.
        
        Args:
            symbol: Stock symbol in Yahoo Finance format
        
        Returns:
            Dict with stock information
        """
        # Return static dummy data for RELIANCE.NS
        if symbol == "RELIANCE.NS":
            logger.info(f"Returning DUMMY stock info for {symbol}")
            return {
                'name': 'Reliance Industries Limited',
                'sector': 'Energy',
                'industry': 'Oil & Gas Refining & Marketing'
            }
        
        # True implementation (commented out for now)
        # try:
        #     ticker = yf.Ticker(symbol)
        #     info = ticker.info
        #     return {
        #         'name': info.get('longName', symbol),
        #         'sector': info.get('sector', ''),
        #         'industry': info.get('industry', '')
        #     }
        # except Exception:
        #     return {
        #         'name': symbol,
        #         'sector': '',
        #         'industry': ''
        #     }
        
        # # For other symbols, return basic info
        logger.warning(f"No dummy data available for {symbol}, returning basic info")
        return {
            'name': symbol,
            'sector': '',
            'industry': ''
        }

"""
Data Provider Interface
Abstracts data provider implementation to decouple business logic from data sources.
"""

from abc import ABC, abstractmethod
from typing import Optional, Dict, Any
import pandas as pd
import yfinance as yf


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
        try:
            ticker = yf.Ticker(symbol)
            data = ticker.history(period=period)
            logger.info(f"Fetched Yahoo data for {symbol}")
            logger.debug(f"Rows: {len(data)}")
            logger.debug(f"Head:\n{data.head()}")
            if data.empty:
                return None
            return data
        except Exception:
            return None
    
    def fetch_stock_info(self, symbol: str) -> Dict[str, Any]:
        """
        Fetch stock information from Yahoo Finance.
        
        Args:
            symbol: Stock symbol in Yahoo Finance format
        
        Returns:
            Dict with stock information
        """
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info
            print(f"[DEBUG] Yahoo info for {symbol}:")
            print(info)
            return {
                'name': info.get('longName', symbol),
                'sector': info.get('sector', ''),
                'industry': info.get('industry', '')
            }
        except Exception:
            return {
                'name': symbol,
                'sector': '',
                'industry': ''
            }

"""
Scouting Agent Tools
Pure business logic functions for screening stocks.
No side effects, stateless, and deterministic.
"""

import pandas as pd
import numpy as np
from typing import List, Optional
from .data_provider import StockDataProvider, YahooFinanceProvider
from .schemas import StockScreeningResult
from logging import Logger, getLogger

logger = getLogger(__name__)

# Nifty 50 stock symbols (as per Yahoo Finance format)``
NIFTY_50_SYMBOLS = [
    "RELIANCE.NS", "TCS.NS", "HDFCBANK.NS", "ICICIBANK.NS", "INFY.NS",
    "HINDUNILVR.NS", "ITC.NS", "SBIN.NS", "BHARTIARTL.NS", "LICI.NS",
    "LT.NS", "HCLTECH.NS", "AXISBANK.NS", "MARUTI.NS", "TITAN.NS",
    "SUNPHARMA.NS", "BAJFINANCE.NS", "ONGC.NS", "WIPRO.NS", "NTPC.NS",
    "NESTLEIND.NS", "POWERGRID.NS", "ULTRACEMCO.NS", "BAJAJFINSV.NS", "COALINDIA.NS",
    "TATAMOTORS.NS", "JSWSTEEL.NS", "HDFCLIFE.NS", "ADANIENT.NS", "ADANIPORTS.NS",
    "TATASTEEL.NS", "DIVISLAB.NS", "SBILIFE.NS", "HINDALCO.NS", "GRASIM.NS",
    "IOC.NS", "ASIANPAINT.NS", "M&M.NS", "ADANIGREEN.NS", "TECHM.NS",
    "BPCL.NS", "HDFC.NS", "APOLLOHOSP.NS", "KOTAKBANK.NS", "MARICO.NS"
    "PIDILITIND.NS", "GODREJCP.NS", "EICHERMOT.NS", "SIEMENS.NS", "DABUR.NS"
]


def get_nifty50_symbols() -> List[str]:
    """
    Returns the list of Nifty 50 stock symbols.
    
    Returns:
        List[str]: List of stock symbols
    """
    return NIFTY_50_SYMBOLS.copy()


def calculate_atr(data: pd.DataFrame, period: int = 14) -> Optional[float]:
    """
    Calculates Average True Range (ATR) for volatility measurement.
    Pure function - no side effects.
    
    Args:
        data: DataFrame with High, Low, Close columns
        period: ATR calculation period (default 14)
    
    Returns:
        float: ATR value, or None if calculation fails
    """
    if data is None or len(data) < period + 1:
        return None
    
    high = data['High'].values
    low = data['Low'].values
    close = data['Close'].values
    
    tr_list = []
    for i in range(1, len(data)):
        tr1 = high[i] - low[i]
        tr2 = abs(high[i] - close[i-1])
        tr3 = abs(low[i] - close[i-1])
        tr = max(tr1, tr2, tr3)
        tr_list.append(tr)
    
    if len(tr_list) < period:
        return None
    
    atr = np.mean(tr_list[-period:])
    return float(atr)


def calculate_atr_percentage(data: pd.DataFrame, period: int = 14) -> Optional[float]:
    """
    Calculates ATR as percentage of current price.
    Pure function - no side effects.
    
    Args:
        data: DataFrame with High, Low, Close columns
        period: ATR calculation period (default 14)
    
    Returns:
        float: ATR percentage (2-5% is target range), or None if calculation fails
    """
    atr = calculate_atr(data, period)
    if atr is None or data is None or len(data) == 0:
        return None
    
    current_price = data['Close'].iloc[-1]
    if current_price == 0:
        return None
    
    atr_percentage = (atr / current_price) * 100
    return float(atr_percentage)


def get_liquidity_metrics(data: pd.DataFrame) -> dict:
    """
    Calculates liquidity metrics (average volume, volume volatility).
    Pure function - no side effects.
    
    Args:
        data: DataFrame with Volume column
    
    Returns:
        Dict with avg_volume, recent_volume, volume_ratio
    """
    if data is None or len(data) == 0 or 'Volume' not in data.columns:
        return {
            'avg_volume': 0.0,
            'recent_volume': 0.0,
            'volume_ratio': 0.0
        }
    
    volumes = data['Volume'].values
    avg_volume = np.mean(volumes)
    
    # Recent volume (last 5 days average)
    recent_period = min(5, len(volumes))
    recent_volume = np.mean(volumes[-recent_period:]) if recent_period > 0 else 0.0
    
    volume_ratio = recent_volume / avg_volume if avg_volume > 0 else 0.0
    
    return {
        'avg_volume': float(avg_volume),
        'recent_volume': float(recent_volume),
        'volume_ratio': float(volume_ratio)
    }


def screen_stock(
    symbol: str,
    data_provider: StockDataProvider
) -> Optional[StockScreeningResult]:
    """
    Screens a single stock for liquidity, volume, and volatility criteria.
    Pure business logic - no side effects.
    
    Args:
        symbol: Stock symbol
        data_provider: Data provider instance
    
    Returns:
        StockScreeningResult if successful, None otherwise
    """
    logger.info(f"fetching historical data for {symbol}")
    # Fetch 3 months of data for better ATR calculation
    data = data_provider.fetch_historical_data(symbol, period="3mo")
    logger.info(f"data: {data}")
    logger.info(f"Fetched {len(data)} rows of data for {symbol}")
    logger.debug(f"Head:\n{data.head()}")
    if data is None or len(data) < 20:  # Need sufficient data
        return None
    
    # Get current stock info
    info = data_provider.fetch_stock_info(symbol)
    current_price = float(data['Close'].iloc[-1])
    company_name = info.get('name', symbol)
    
    # Calculate ATR percentage
    atr_percentage = calculate_atr_percentage(data, period=14)
    
    # Calculate liquidity metrics
    liquidity = get_liquidity_metrics(data)
    
    # Screen criteria:
    # 1. ATR between 2% and 5%
    # 2. Recent volume should be at least 80% of average volume (indicating active trading)
    # 3. Average volume should be significant (at least 100k)
    
    meets_criteria = True
    criteria_details = []
    
    if atr_percentage is None:
        meets_criteria = False
        criteria_details.append("ATR calculation failed")
    elif atr_percentage < 2.0:
        meets_criteria = False
        criteria_details.append(f"ATR too low: {atr_percentage:.2f}%")
    elif atr_percentage > 5.0:
        meets_criteria = False
        criteria_details.append(f"ATR too high: {atr_percentage:.2f}%")
    else:
        criteria_details.append(f"ATR OK: {atr_percentage:.2f}%")
    
    # Volume check - recent volume should be at least 80% of average
    if liquidity['volume_ratio'] < 0.8:
        meets_criteria = False
        criteria_details.append(f"Volume ratio low: {liquidity['volume_ratio']:.2f}")
    else:
        criteria_details.append(f"Volume ratio OK: {liquidity['volume_ratio']:.2f}")
    
    # Minimum volume threshold (100k)
    if liquidity['avg_volume'] < 100000:
        meets_criteria = False
        criteria_details.append(f"Avg volume too low: {liquidity['avg_volume']:.0f}")
    else:
        criteria_details.append(f"Avg volume OK: {liquidity['avg_volume']:.0f}")
    
    return StockScreeningResult(
        symbol=symbol,
        name=company_name,
        current_price=current_price,
        atr_percentage=atr_percentage,
        avg_volume=liquidity['avg_volume'],
        recent_volume=liquidity['recent_volume'],
        volume_ratio=liquidity['volume_ratio'],
        meets_criteria=meets_criteria,
        criteria_details=criteria_details
    )


def screen_stocks(
    symbols: List[str],
    data_provider: StockDataProvider
) -> List[StockScreeningResult]:
    """
    Screens multiple stocks.
    Pure function - no side effects.
    
    Args:
        symbols: List of stock symbols to screen
        data_provider: Data provider instance
    
    Returns:
        List of screening results
    """
    results = []
    logger.info(f"Screening {len(symbols)} stocks")
    logger.debug(f"Symbols: {symbols}")
    for symbol in symbols:
        result = screen_stock(symbol, data_provider)
        if result:
            results.append(result)
    
    return results


def calculate_score(stock: StockScreeningResult) -> float:
    """
    Calculate a score for a stock based on screening criteria.
    Pure function - no side effects.
    
    Args:
        stock: Stock screening result
    
    Returns:
        float: Score (higher is better)
    """
    score = 0.0
    
    # ATR score (prefer 2-5%, best around 3.5%)
    if stock.atr_percentage:
        if 2.0 <= stock.atr_percentage <= 5.0:
            score += 50.0 - abs(stock.atr_percentage - 3.5) * 10.0
        else:
            score -= 20.0
    
    # Volume ratio score
    score += stock.volume_ratio * 30.0
    
    # Volume magnitude score (normalized)
    score += min(stock.avg_volume / 1000000.0, 1.0) * 20.0  # Cap at 1M volume
    
    return score


def shortlist_stocks(
    results: List[StockScreeningResult],
    top_n: int = 10
) -> List[StockScreeningResult]:
    """
    Shortlists top N stocks that meet the screening criteria.
    Pure function - no side effects, deterministic.
    
    Args:
        results: List of screening results
        top_n: Number of stocks to shortlist (default 10)
    
    Returns:
        List of shortlisted stocks
    """
    # Filter stocks that meet criteria
    qualifying_stocks = [r for r in results if r.meets_criteria]
    
    # If we have enough qualifying stocks, return top N
    if len(qualifying_stocks) >= top_n:
        # Sort by volume ratio (descending) and ATR percentage (closer to 3.5%)
        qualifying_stocks.sort(
            key=lambda x: (
                x.volume_ratio,
                -abs(x.atr_percentage - 3.5) if x.atr_percentage else 0.0
            ),
            reverse=True
        )
        return qualifying_stocks[:top_n]
    
    # If not enough qualify, score all stocks and take top N
    scored_results = []
    for stock in results:
        score = calculate_score(stock)
        # Create a copy with score
        scored_stock = StockScreeningResult(
            symbol=stock.symbol,
            name=stock.name,
            current_price=stock.current_price,
            atr_percentage=stock.atr_percentage,
            avg_volume=stock.avg_volume,
            recent_volume=stock.recent_volume,
            volume_ratio=stock.volume_ratio,
            meets_criteria=stock.meets_criteria,
            criteria_details=stock.criteria_details,
            score=score
        )
        scored_results.append(scored_stock)
    
    # Sort by score descending
    scored_results.sort(key=lambda x: x.score or 0.0, reverse=True)
    
    return scored_results[:top_n]

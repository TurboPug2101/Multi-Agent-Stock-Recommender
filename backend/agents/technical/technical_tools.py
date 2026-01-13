"""
Technical Analysis Tools
Pure business logic functions for technical analysis.
No side effects, stateless, and deterministic.
"""

import pandas as pd
import numpy as np
from typing import Optional, List
import logging
from .technical_schemas import TechnicalIndicators, TechnicalAnalysisResult

logger = logging.getLogger(__name__)

def calculate_rsi(prices: pd.Series, period: int = 14) -> Optional[float]:
    """
    Calculate Relative Strength Index.
    
    Args:
        prices: Series of closing prices
        period: RSI period (default 14)
    
    Returns:
        RSI value (0-100) or None
    """
    if len(prices) < period + 1:
        return None
    
    # Calculate price changes
    delta = prices.diff()
    
    # Separate gains and losses
    gains = delta.where(delta > 0, 0)
    losses = -delta.where(delta < 0, 0)
    
    # Calculate average gains and losses
    avg_gain = gains.rolling(window=period).mean()
    avg_loss = losses.rolling(window=period).mean()
    
    # Calculate RS and RSI
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    
    return float(rsi.iloc[-1]) if not pd.isna(rsi.iloc[-1]) else None


def calculate_macd(prices: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9):
    """
    Calculate MACD (Moving Average Convergence Divergence).
    
    Args:
        prices: Series of closing prices
        fast: Fast EMA period
        slow: Slow EMA period
        signal: Signal line period
    
    Returns:
        Tuple of (macd_line, signal_line, histogram) or (None, None, None)
    """
    if len(prices) < slow + signal:
        return None, None, None
    
    # Calculate EMAs
    ema_fast = prices.ewm(span=fast, adjust=False).mean()
    ema_slow = prices.ewm(span=slow, adjust=False).mean()
    
    # MACD line
    macd_line = ema_fast - ema_slow
    
    # Signal line
    signal_line = macd_line.ewm(span=signal, adjust=False).mean()
    
    # Histogram
    histogram = macd_line - signal_line
    
    return (
        float(macd_line.iloc[-1]) if not pd.isna(macd_line.iloc[-1]) else None,
        float(signal_line.iloc[-1]) if not pd.isna(signal_line.iloc[-1]) else None,
        float(histogram.iloc[-1]) if not pd.isna(histogram.iloc[-1]) else None
    )


def calculate_moving_averages(prices: pd.Series):
    """
    Calculate various moving averages.
    
    Args:
        prices: Series of closing prices
    
    Returns:
        Dict with SMA and EMA values
    """
    result = {}
    
    # SMAs
    if len(prices) >= 20:
        result['sma_20'] = float(prices.rolling(window=20).mean().iloc[-1])
    else:
        result['sma_20'] = None
    
    if len(prices) >= 50:
        result['sma_50'] = float(prices.rolling(window=50).mean().iloc[-1])
    else:
        result['sma_50'] = None
    
    # EMAs
    if len(prices) >= 12:
        result['ema_12'] = float(prices.ewm(span=12, adjust=False).mean().iloc[-1])
    else:
        result['ema_12'] = None
    
    if len(prices) >= 26:
        result['ema_26'] = float(prices.ewm(span=26, adjust=False).mean().iloc[-1])
    else:
        result['ema_26'] = None
    
    return result


def determine_trend(current_price: float, sma_20: Optional[float], sma_50: Optional[float]) -> str:
    """
    Determine trend based on moving averages.
    
    Args:
        current_price: Current stock price
        sma_20: 20-day SMA
        sma_50: 50-day SMA
    
    Returns:
        'bullish', 'bearish', or 'neutral'
    """
    if sma_20 is None or sma_50 is None:
        return 'neutral'
    
    # Price above both SMAs and SMA20 > SMA50 = bullish
    if current_price > sma_20 > sma_50:
        return 'bullish'
    
    # Price below both SMAs and SMA20 < SMA50 = bearish
    if current_price < sma_20 < sma_50:
        return 'bearish'
    
    return 'neutral'


def generate_signals(rsi: Optional[float], macd: Optional[float], 
                     macd_signal: Optional[float], trend: str) -> List[str]:
    """
    Generate trading signals based on indicators.
    
    Args:
        rsi: RSI value
        macd: MACD line value
        macd_signal: MACD signal line value
        trend: Current trend
    
    Returns:
        List of signal strings
    """
    signals = []
    
    # RSI signals
    if rsi is not None:
        if rsi < 30:
            signals.append("RSI Oversold (<30)")
        elif rsi > 70:
            signals.append("RSI Overbought (>70)")
        elif 40 <= rsi <= 60:
            signals.append("RSI Neutral")
    
    # MACD signals
    if macd is not None and macd_signal is not None:
        if macd > macd_signal:
            signals.append("MACD Bullish (above signal)")
        else:
            signals.append("MACD Bearish (below signal)")
    
    # Trend signals
    signals.append(f"Trend: {trend.capitalize()}")
    
    return signals


def calculate_strength_score(rsi: Optional[float], macd_histogram: Optional[float], 
                             trend: str) -> float:
    """
    Calculate overall strength score (0-100).
    
    Args:
        rsi: RSI value
        macd_histogram: MACD histogram value
        trend: Current trend
    
    Returns:
        Strength score (0-100)
    """
    score = 50.0  # Start neutral
    
    # RSI contribution (±20 points)
    if rsi is not None:
        if rsi < 30:
            score += 20  # Oversold = potential buy
        elif rsi > 70:
            score -= 20  # Overbought = potential sell
        elif 40 <= rsi <= 60:
            score += 5  # Neutral is slightly positive
    
    # MACD contribution (±15 points)
    if macd_histogram is not None:
        if macd_histogram > 0:
            score += min(15, macd_histogram * 10)
        else:
            score -= min(15, abs(macd_histogram) * 10)
    
    # Trend contribution (±15 points)
    if trend == 'bullish':
        score += 15
    elif trend == 'bearish':
        score -= 15
    
    # Clamp to 0-100
    return max(0, min(100, score))


def determine_recommendation(strength: float, trend: str) -> str:
    """
    Determine recommendation based on strength and trend.
    
    Args:
        strength: Strength score (0-100)
        trend: Current trend
    
    Returns:
        'strong_buy', 'buy', 'hold', 'sell', or 'strong_sell'
    """
    if strength >= 70:
        return 'strong_buy'
    elif strength >= 55:
        return 'buy'
    elif strength >= 45:
        return 'hold'
    elif strength >= 30:
        return 'sell'
    else:
        return 'strong_sell'


def analyze_stock_technical(symbol: str, name: str, current_price: float, 
                            data_provider) -> Optional[TechnicalAnalysisResult]:
    """
    Perform technical analysis on a single stock.
    
    Args:
        symbol: Stock symbol
        name: Stock name
        current_price: Current price
        data_provider: Data provider instance
    
    Returns:
        TechnicalAnalysisResult or None
    """
    try:
        # Fetch historical data (3 months for better indicators)
        data = data_provider.fetch_historical_data(symbol, period="3mo")
        
        if data is None or len(data) < 50:
            logger.warning(f"Insufficient data for {symbol}")
            return None
        
        prices = data['Close']
        
        # Calculate indicators
        rsi = calculate_rsi(prices)
        macd, macd_signal, macd_histogram = calculate_macd(prices)
        mas = calculate_moving_averages(prices)
        
        indicators = TechnicalIndicators(
            rsi=rsi,
            macd=macd,
            macd_signal=macd_signal,
            macd_histogram=macd_histogram,
            sma_20=mas.get('sma_20'),
            sma_50=mas.get('sma_50'),
            ema_12=mas.get('ema_12'),
            ema_26=mas.get('ema_26')
        )
        
        # Determine trend
        trend = determine_trend(current_price, mas.get('sma_20'), mas.get('sma_50'))
        
        # Generate signals
        signals = generate_signals(rsi, macd, macd_signal, trend)
        
        # Calculate strength
        strength = calculate_strength_score(rsi, macd_histogram, trend)
        
        # Determine recommendation
        recommendation = determine_recommendation(strength, trend)
        
        logger.info(f"✓ {symbol}: Analyzed - {trend.upper()}, Strength: {strength:.1f}, {recommendation.upper()}")
        
        return TechnicalAnalysisResult(
            symbol=symbol,
            name=name,
            current_price=current_price,
            indicators=indicators,
            trend=trend,
            strength=strength,
            signals=signals,
            recommendation=recommendation
        )
    
    except Exception as e:
        logger.error(f"Error analyzing {symbol}: {e}")
        return None
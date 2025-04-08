import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Union


def moving_average(data: List[float], period: int = 20) -> List[float]:
    """
    Calculate Simple Moving Average (SMA)
    
    Args:
        data: List of price data (typically closing prices)
        period: MA period
        
    Returns:
        List of SMA values
    """
    if len(data) < period:
        # Return list of NaNs of the same length as data
        return [np.nan] * len(data)
    
    ma_values = []
    for i in range(len(data)):
        if i < period - 1:
            ma_values.append(np.nan)
        else:
            ma_values.append(sum(data[i-(period-1):i+1]) / period)
    
    return ma_values


def exponential_moving_average(data: List[float], period: int = 20) -> List[float]:
    """
    Calculate Exponential Moving Average (EMA)
    
    Args:
        data: List of price data (typically closing prices)
        period: EMA period
        
    Returns:
        List of EMA values
    """
    if len(data) < period:
        return [np.nan] * len(data)
    
    # Calculate multiplier
    multiplier = 2 / (period + 1)
    
    # Calculate initial SMA
    sma = sum(data[:period]) / period
    
    # Initialize EMA values with NaNs
    ema_values = [np.nan] * (period - 1)
    
    # Add initial SMA value
    ema_values.append(sma)
    
    # Calculate EMA for remaining data points
    for i in range(period, len(data)):
        ema = (data[i] - ema_values[-1]) * multiplier + ema_values[-1]
        ema_values.append(ema)
    
    return ema_values


def relative_strength_index(data: List[float], period: int = 14) -> List[float]:
    """
    Calculate Relative Strength Index (RSI)
    
    Args:
        data: List of price data (typically closing prices)
        period: RSI period
        
    Returns:
        List of RSI values
    """
    if len(data) < period + 1:
        return [np.nan] * len(data)
    
    # Calculate price changes
    changes = [data[i] - data[i-1] for i in range(1, len(data))]
    
    # Initialize RSI values with NaNs
    rsi_values = [np.nan] * period
    
    # Calculate initial average gains and losses
    gains = [max(0, change) for change in changes[:period]]
    losses = [max(0, -change) for change in changes[:period]]
    
    avg_gain = sum(gains) / period
    avg_loss = sum(losses) / period
    
    # Calculate RSI for remaining data points
    for i in range(period, len(data) - 1):
        change = changes[i]
        gain = max(0, change)
        loss = max(0, -change)
        
        # Use smoothed averages (Wilder's method)
        avg_gain = (avg_gain * (period - 1) + gain) / period
        avg_loss = (avg_loss * (period - 1) + loss) / period
        
        if avg_loss == 0:
            rsi = 100
        else:
            rs = avg_gain / avg_loss
            rsi = 100 - (100 / (1 + rs))
        
        rsi_values.append(rsi)
    
    # Add extra NaN to match the length of input data
    if len(rsi_values) < len(data):
        rsi_values.append(np.nan)
    
    return rsi_values


def macd(data: List[float], fast_period: int = 12, slow_period: int = 26, 
         signal_period: int = 9) -> Dict[str, List[float]]:
    """
    Calculate Moving Average Convergence Divergence (MACD)
    
    Args:
        data: List of price data (typically closing prices)
        fast_period: Fast EMA period
        slow_period: Slow EMA period
        signal_period: MACD signal line period
        
    Returns:
        Dictionary with MACD, MACD Signal, and MACD Histogram values
    """
    if len(data) < slow_period + signal_period:
        return {
            "macd": [np.nan] * len(data),
            "signal": [np.nan] * len(data),
            "histogram": [np.nan] * len(data)
        }
    
    # Calculate fast and slow EMAs
    fast_ema = exponential_moving_average(data, fast_period)
    slow_ema = exponential_moving_average(data, slow_period)
    
    # Calculate MACD line
    macd_line = [np.nan] * len(data)
    for i in range(len(data)):
        if np.isnan(fast_ema[i]) or np.isnan(slow_ema[i]):
            continue
        macd_line[i] = fast_ema[i] - slow_ema[i]
    
    # Calculate signal line (EMA of MACD line)
    # Remove NaN values for calculation
    valid_macd = []
    for val in macd_line:
        if not np.isnan(val):
            valid_macd.append(val)
    
    # Ensure we have enough data for the signal line EMA
    if len(valid_macd) < signal_period:
        return {
            "macd": macd_line,
            "signal": [np.nan] * len(data),
            "histogram": [np.nan] * len(data)
        }
    
    # Calculate EMA of valid MACD values
    valid_signal = []
    
    # Initialize with SMA
    valid_signal.append(sum(valid_macd[:signal_period]) / signal_period)
    
    # Calculate EMA for remaining points
    multiplier = 2 / (signal_period + 1)
    for i in range(signal_period, len(valid_macd)):
        signal_val = (valid_macd[i] - valid_signal[-1]) * multiplier + valid_signal[-1]
        valid_signal.append(signal_val)
    
    # Map signal line back to original data length
    signal_line = [np.nan] * len(data)
    valid_idx = 0
    
    for i in range(len(data)):
        if not np.isnan(macd_line[i]):
            valid_idx += 1
            if valid_idx > signal_period:
                signal_line[i] = valid_signal[valid_idx - signal_period - 1]
    
    # Calculate histogram
    histogram = [np.nan] * len(data)
    for i in range(len(data)):
        if not np.isnan(macd_line[i]) and not np.isnan(signal_line[i]):
            histogram[i] = macd_line[i] - signal_line[i]
    
    return {
        "macd": macd_line,
        "signal": signal_line,
        "histogram": histogram
    }


def bollinger_bands(data: List[float], period: int = 20, 
                   std_dev: float = 2.0) -> Dict[str, List[float]]:
    """
    Calculate Bollinger Bands
    
    Args:
        data: List of price data (typically closing prices)
        period: Bollinger Bands period
        std_dev: Standard deviation multiplier
        
    Returns:
        Dictionary with upper, middle, and lower band values
    """
    if len(data) < period:
        return {
            "upper": [np.nan] * len(data),
            "middle": [np.nan] * len(data),
            "lower": [np.nan] * len(data)
        }
    
    # Calculate SMA (middle band)
    middle_band = moving_average(data, period)
    
    # Calculate standard deviation
    upper_band = [np.nan] * len(data)
    lower_band = [np.nan] * len(data)
    
    for i in range(period - 1, len(data)):
        window = data[i-(period-1):i+1]
        std = np.std(window)
        upper_band[i] = middle_band[i] + (std_dev * std)
        lower_band[i] = middle_band[i] - (std_dev * std)
    
    return {
        "upper": upper_band,
        "middle": middle_band,
        "lower": lower_band
    }


def stochastic_oscillator(high_data: List[float], low_data: List[float], 
                         close_data: List[float], k_period: int = 14, 
                         d_period: int = 3) -> Dict[str, List[float]]:
    """
    Calculate Stochastic Oscillator
    
    Args:
        high_data: List of high prices
        low_data: List of low prices
        close_data: List of closing prices
        k_period: %K period
        d_period: %D period
        
    Returns:
        Dictionary with %K and %D values
    """
    if len(close_data) < k_period + d_period - 1:
        return {
            "k": [np.nan] * len(close_data),
            "d": [np.nan] * len(close_data)
        }
    
    # Calculate %K
    k_values = [np.nan] * len(close_data)
    
    for i in range(k_period - 1, len(close_data)):
        # Get highest high and lowest low in the period
        highest_high = max(high_data[i-(k_period-1):i+1])
        lowest_low = min(low_data[i-(k_period-1):i+1])
        
        # Calculate %K
        if highest_high == lowest_low:
            k = 50  # Middle value if range is zero
        else:
            k = 100 * ((close_data[i] - lowest_low) / (highest_high - lowest_low))
        
        k_values[i] = k
    
    # Calculate %D (SMA of %K)
    d_values = [np.nan] * len(close_data)
    
    for i in range(k_period + d_period - 2, len(close_data)):
        # Calculate SMA of the last d_period %K values
        d = sum(k_values[i-(d_period-1):i+1]) / d_period
        d_values[i] = d
    
    return {
        "k": k_values,
        "d": d_values
    }


def calculate_indicators(ohlcv_data: List[Dict]) -> Dict:
    """
    Calculate multiple indicators based on OHLCV data
    
    Args:
        ohlcv_data: List of OHLCV dictionaries from the exchange
        
    Returns:
        Dictionary of calculated indicators
    """
    if not ohlcv_data:
        return {}
    
    # Extract individual data series
    close_prices = [candle['close'] for candle in ohlcv_data]
    high_prices = [candle['high'] for candle in ohlcv_data]
    low_prices = [candle['low'] for candle in ohlcv_data]
    
    # Calculate indicators
    results = {
        "sma_20": moving_average(close_prices, 20),
        "sma_50": moving_average(close_prices, 50),
        "sma_200": moving_average(close_prices, 200),
        "ema_12": exponential_moving_average(close_prices, 12),
        "ema_26": exponential_moving_average(close_prices, 26),
        "rsi_14": relative_strength_index(close_prices, 14),
        "macd": macd(close_prices),
        "bollinger": bollinger_bands(close_prices),
        "stochastic": stochastic_oscillator(high_prices, low_prices, close_prices)
    }
    
    return results

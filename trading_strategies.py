import numpy as np
from typing import Dict, List, Optional, Union, Tuple
import logging
from indicators import calculate_indicators

logger = logging.getLogger(__name__)

class TradingStrategy:
    """Base class for trading strategies"""
    
    def __init__(self, name: str, description: str, parameters: Dict = None):
        """
        Initialize a trading strategy
        
        Args:
            name: Strategy name
            description: Strategy description
            parameters: Dictionary of strategy parameters
        """
        self.name = name
        self.description = description
        self.parameters = parameters or {}
        
    def analyze(self, ohlcv_data: List[Dict]) -> Dict:
        """
        Analyze market data and generate signals
        
        Args:
            ohlcv_data: List of OHLCV data dictionaries
            
        Returns:
            Dictionary with analysis results
        """
        raise NotImplementedError("Subclasses must implement analyze method")
    
    def get_signal(self, ohlcv_data: List[Dict]) -> str:
        """
        Get trading signal based on market data
        
        Args:
            ohlcv_data: List of OHLCV data dictionaries
            
        Returns:
            Signal string: 'BUY', 'SELL', or 'NEUTRAL'
        """
        raise NotImplementedError("Subclasses must implement get_signal method")


class MACrossoverStrategy(TradingStrategy):
    """Moving Average Crossover Strategy"""
    
    def __init__(self, parameters: Dict = None):
        """
        Initialize MA Crossover Strategy
        
        Args:
            parameters: Dictionary with 'fast_period' and 'slow_period'
        """
        default_params = {
            "fast_period": 20,
            "slow_period": 50
        }
        
        # Update default parameters with provided ones
        if parameters:
            default_params.update(parameters)
            
        super().__init__(
            name="Moving Average Crossover",
            description="Generate signals based on moving average crossovers",
            parameters=default_params
        )
    
    def analyze(self, ohlcv_data: List[Dict]) -> Dict:
        """
        Analyze market data using MA crossover
        
        Args:
            ohlcv_data: List of OHLCV data dictionaries
            
        Returns:
            Dictionary with analysis results
        """
        if not ohlcv_data or len(ohlcv_data) < self.parameters["slow_period"]:
            return {"error": "Insufficient data for analysis"}
        
        # Calculate indicators
        indicators = calculate_indicators(ohlcv_data)
        
        # Get MA values based on parameters
        fast_key = f"sma_{self.parameters['fast_period']}"
        slow_key = f"sma_{self.parameters['slow_period']}"
        
        # Use default MAs if the requested ones aren't available
        if fast_key not in indicators:
            fast_ma = indicators.get("sma_20", [])
        else:
            fast_ma = indicators[fast_key]
            
        if slow_key not in indicators:
            slow_ma = indicators.get("sma_50", [])
        else:
            slow_ma = indicators[slow_key]
        
        # Get the most recent valid values
        latest_fast = next((x for x in reversed(fast_ma) if not np.isnan(x)), None)
        latest_slow = next((x for x in reversed(slow_ma) if not np.isnan(x)), None)
        
        # Get previous values
        prev_idx = -2
        prev_fast = None
        prev_slow = None
        
        if len(fast_ma) > 1 and len(slow_ma) > 1:
            while prev_idx >= -len(fast_ma) and (prev_fast is None or prev_slow is None):
                if not np.isnan(fast_ma[prev_idx]):
                    prev_fast = fast_ma[prev_idx]
                if not np.isnan(slow_ma[prev_idx]):
                    prev_slow = slow_ma[prev_idx]
                prev_idx -= 1
        
        result = {
            "fast_ma": fast_ma,
            "slow_ma": slow_ma,
            "latest_fast": latest_fast,
            "latest_slow": latest_slow,
            "prev_fast": prev_fast,
            "prev_slow": prev_slow,
            "signal": "NEUTRAL"
        }
        
        # Determine signal
        if latest_fast and latest_slow and prev_fast and prev_slow:
            if latest_fast > latest_slow and prev_fast <= prev_slow:
                result["signal"] = "BUY"
            elif latest_fast < latest_slow and prev_fast >= prev_slow:
                result["signal"] = "SELL"
        
        return result
    
    def get_signal(self, ohlcv_data: List[Dict]) -> str:
        """
        Get trading signal based on MA crossover
        
        Args:
            ohlcv_data: List of OHLCV data dictionaries
            
        Returns:
            Signal string: 'BUY', 'SELL', or 'NEUTRAL'
        """
        analysis = self.analyze(ohlcv_data)
        return analysis.get("signal", "NEUTRAL")


class RSIStrategy(TradingStrategy):
    """RSI Overbought/Oversold Strategy"""
    
    def __init__(self, parameters: Dict = None):
        """
        Initialize RSI Strategy
        
        Args:
            parameters: Dictionary with 'period', 'oversold', and 'overbought' thresholds
        """
        default_params = {
            "period": 14,
            "oversold": 30,
            "overbought": 70
        }
        
        # Update default parameters with provided ones
        if parameters:
            default_params.update(parameters)
            
        super().__init__(
            name="RSI Strategy",
            description="Generate signals based on RSI overbought/oversold conditions",
            parameters=default_params
        )
    
    def analyze(self, ohlcv_data: List[Dict]) -> Dict:
        """
        Analyze market data using RSI
        
        Args:
            ohlcv_data: List of OHLCV data dictionaries
            
        Returns:
            Dictionary with analysis results
        """
        if not ohlcv_data or len(ohlcv_data) < self.parameters["period"]:
            return {"error": "Insufficient data for analysis"}
        
        # Calculate indicators
        indicators = calculate_indicators(ohlcv_data)
        
        # Get RSI values
        rsi_key = f"rsi_{self.parameters['period']}"
        if rsi_key not in indicators:
            rsi = indicators.get("rsi_14", [])
        else:
            rsi = indicators[rsi_key]
        
        # Get the latest valid RSI value
        latest_rsi = next((x for x in reversed(rsi) if not np.isnan(x)), None)
        
        # Get previous RSI value
        prev_idx = -2
        prev_rsi = None
        
        if len(rsi) > 1:
            while prev_idx >= -len(rsi) and prev_rsi is None:
                if not np.isnan(rsi[prev_idx]):
                    prev_rsi = rsi[prev_idx]
                prev_idx -= 1
        
        result = {
            "rsi": rsi,
            "latest_rsi": latest_rsi,
            "prev_rsi": prev_rsi,
            "signal": "NEUTRAL"
        }
        
        # Determine signal
        if latest_rsi is not None and prev_rsi is not None:
            if latest_rsi < self.parameters["oversold"] and prev_rsi >= self.parameters["oversold"]:
                result["signal"] = "BUY"
            elif latest_rsi > self.parameters["overbought"] and prev_rsi <= self.parameters["overbought"]:
                result["signal"] = "SELL"
        
        return result
    
    def get_signal(self, ohlcv_data: List[Dict]) -> str:
        """
        Get trading signal based on RSI
        
        Args:
            ohlcv_data: List of OHLCV data dictionaries
            
        Returns:
            Signal string: 'BUY', 'SELL', or 'NEUTRAL'
        """
        analysis = self.analyze(ohlcv_data)
        return analysis.get("signal", "NEUTRAL")


class MACDStrategy(TradingStrategy):
    """MACD Crossover Strategy"""
    
    def __init__(self, parameters: Dict = None):
        """
        Initialize MACD Strategy
        
        Args:
            parameters: Dictionary with MACD parameters
        """
        default_params = {
            "fast_period": 12,
            "slow_period": 26,
            "signal_period": 9
        }
        
        # Update default parameters with provided ones
        if parameters:
            default_params.update(parameters)
            
        super().__init__(
            name="MACD Crossover",
            description="Generate signals based on MACD line crossing signal line",
            parameters=default_params
        )
    
    def analyze(self, ohlcv_data: List[Dict]) -> Dict:
        """
        Analyze market data using MACD
        
        Args:
            ohlcv_data: List of OHLCV data dictionaries
            
        Returns:
            Dictionary with analysis results
        """
        if not ohlcv_data or len(ohlcv_data) < self.parameters["slow_period"] + self.parameters["signal_period"]:
            return {"error": "Insufficient data for analysis"}
        
        # Calculate indicators
        indicators = calculate_indicators(ohlcv_data)
        
        # Get MACD values
        macd_data = indicators.get("macd", {})
        macd_line = macd_data.get("macd", [])
        signal_line = macd_data.get("signal", [])
        histogram = macd_data.get("histogram", [])
        
        # Get the latest valid values
        latest_macd = next((x for x in reversed(macd_line) if not np.isnan(x)), None)
        latest_signal = next((x for x in reversed(signal_line) if not np.isnan(x)), None)
        
        # Get previous values
        prev_idx = -2
        prev_macd = None
        prev_signal = None
        
        if len(macd_line) > 1 and len(signal_line) > 1:
            while prev_idx >= -len(macd_line) and (prev_macd is None or prev_signal is None):
                if not np.isnan(macd_line[prev_idx]):
                    prev_macd = macd_line[prev_idx]
                if not np.isnan(signal_line[prev_idx]):
                    prev_signal = signal_line[prev_idx]
                prev_idx -= 1
        
        result = {
            "macd_line": macd_line,
            "signal_line": signal_line,
            "histogram": histogram,
            "latest_macd": latest_macd,
            "latest_signal": latest_signal,
            "prev_macd": prev_macd,
            "prev_signal": prev_signal,
            "signal": "NEUTRAL"
        }
        
        # Determine signal
        if latest_macd and latest_signal and prev_macd and prev_signal:
            if latest_macd > latest_signal and prev_macd <= prev_signal:
                result["signal"] = "BUY"
            elif latest_macd < latest_signal and prev_macd >= prev_signal:
                result["signal"] = "SELL"
        
        return result
    
    def get_signal(self, ohlcv_data: List[Dict]) -> str:
        """
        Get trading signal based on MACD
        
        Args:
            ohlcv_data: List of OHLCV data dictionaries
            
        Returns:
            Signal string: 'BUY', 'SELL', or 'NEUTRAL'
        """
        analysis = self.analyze(ohlcv_data)
        return analysis.get("signal", "NEUTRAL")


class BollingerBandsStrategy(TradingStrategy):
    """Bollinger Bands Strategy"""
    
    def __init__(self, parameters: Dict = None):
        """
        Initialize Bollinger Bands Strategy
        
        Args:
            parameters: Dictionary with Bollinger Bands parameters
        """
        default_params = {
            "period": 20,
            "std_dev": 2.0,
            "use_close_price": True  # If True, use close price instead of SMA for band touch
        }
        
        # Update default parameters with provided ones
        if parameters:
            default_params.update(parameters)
            
        super().__init__(
            name="Bollinger Bands Strategy",
            description="Generate signals based on price touching Bollinger Bands",
            parameters=default_params
        )
    
    def analyze(self, ohlcv_data: List[Dict]) -> Dict:
        """
        Analyze market data using Bollinger Bands
        
        Args:
            ohlcv_data: List of OHLCV data dictionaries
            
        Returns:
            Dictionary with analysis results
        """
        if not ohlcv_data or len(ohlcv_data) < self.parameters["period"]:
            return {"error": "Insufficient data for analysis"}
        
        # Calculate indicators
        indicators = calculate_indicators(ohlcv_data)
        
        # Get Bollinger Bands values
        bb_data = indicators.get("bollinger", {})
        upper_band = bb_data.get("upper", [])
        middle_band = bb_data.get("middle", [])
        lower_band = bb_data.get("lower", [])
        
        # Get close prices
        close_prices = [candle['close'] for candle in ohlcv_data]
        
        # Get the latest valid values
        latest_upper = next((x for x in reversed(upper_band) if not np.isnan(x)), None)
        latest_middle = next((x for x in reversed(middle_band) if not np.isnan(x)), None)
        latest_lower = next((x for x in reversed(lower_band) if not np.isnan(x)), None)
        latest_close = close_prices[-1] if close_prices else None
        
        # Get previous values
        prev_upper = upper_band[-2] if len(upper_band) > 1 and not np.isnan(upper_band[-2]) else None
        prev_lower = lower_band[-2] if len(lower_band) > 1 and not np.isnan(lower_band[-2]) else None
        prev_close = close_prices[-2] if len(close_prices) > 1 else None
        
        result = {
            "upper_band": upper_band,
            "middle_band": middle_band,
            "lower_band": lower_band,
            "close_prices": close_prices,
            "latest_upper": latest_upper,
            "latest_middle": latest_middle,
            "latest_lower": latest_lower,
            "latest_close": latest_close,
            "signal": "NEUTRAL"
        }
        
        # Determine signal
        if latest_upper and latest_lower and latest_close and prev_upper and prev_lower and prev_close:
            # Check if price touched or crossed the lower band (buy signal)
            if latest_close <= latest_lower and prev_close > prev_lower:
                result["signal"] = "BUY"
            # Check if price touched or crossed the upper band (sell signal)
            elif latest_close >= latest_upper and prev_close < prev_upper:
                result["signal"] = "SELL"
        
        return result
    
    def get_signal(self, ohlcv_data: List[Dict]) -> str:
        """
        Get trading signal based on Bollinger Bands
        
        Args:
            ohlcv_data: List of OHLCV data dictionaries
            
        Returns:
            Signal string: 'BUY', 'SELL', or 'NEUTRAL'
        """
        analysis = self.analyze(ohlcv_data)
        return analysis.get("signal", "NEUTRAL")


def get_strategy_by_name(strategy_name: str, parameters: Dict = None) -> Optional[TradingStrategy]:
    """
    Factory function to get a strategy instance by name
    
    Args:
        strategy_name: Name of the strategy to create
        parameters: Parameters for the strategy
        
    Returns:
        TradingStrategy instance or None if not found
    """
    strategy_map = {
        "MA_CROSSOVER": MACrossoverStrategy,
        "RSI": RSIStrategy,
        "MACD": MACDStrategy,
        "BOLLINGER_BANDS": BollingerBandsStrategy
    }
    
    strategy_class = strategy_map.get(strategy_name.upper())
    if strategy_class:
        return strategy_class(parameters)
    else:
        logger.error(f"Strategy '{strategy_name}' not found")
        return None


def get_available_strategies() -> List[Dict]:
    """
    Get information about all available strategies
    
    Returns:
        List of strategy information dictionaries
    """
    strategies = [
        {
            "id": "MA_CROSSOVER",
            "name": "Moving Average Crossover",
            "description": "Generate signals based on moving average crossovers",
            "parameters": {
                "fast_period": {"type": "int", "default": 20, "min": 3, "max": 200, "description": "Fast MA period"},
                "slow_period": {"type": "int", "default": 50, "min": 5, "max": 200, "description": "Slow MA period"}
            }
        },
        {
            "id": "RSI",
            "name": "RSI Strategy",
            "description": "Generate signals based on RSI overbought/oversold conditions",
            "parameters": {
                "period": {"type": "int", "default": 14, "min": 2, "max": 50, "description": "RSI period"},
                "oversold": {"type": "int", "default": 30, "min": 10, "max": 40, "description": "Oversold threshold"},
                "overbought": {"type": "int", "default": 70, "min": 60, "max": 90, "description": "Overbought threshold"}
            }
        },
        {
            "id": "MACD",
            "name": "MACD Crossover",
            "description": "Generate signals based on MACD line crossing signal line",
            "parameters": {
                "fast_period": {"type": "int", "default": 12, "min": 5, "max": 50, "description": "Fast EMA period"},
                "slow_period": {"type": "int", "default": 26, "min": 10, "max": 100, "description": "Slow EMA period"},
                "signal_period": {"type": "int", "default": 9, "min": 3, "max": 30, "description": "Signal line period"}
            }
        },
        {
            "id": "BOLLINGER_BANDS",
            "name": "Bollinger Bands Strategy",
            "description": "Generate signals based on price touching Bollinger Bands",
            "parameters": {
                "period": {"type": "int", "default": 20, "min": 5, "max": 50, "description": "BB period"},
                "std_dev": {"type": "float", "default": 2.0, "min": 1.0, "max": 4.0, "description": "Standard deviation multiplier"},
                "use_close_price": {"type": "bool", "default": True, "description": "Use close price instead of SMA for band touch"}
            }
        }
    ]
    
    return strategies

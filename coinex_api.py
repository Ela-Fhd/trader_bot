import os
import ccxt
import logging
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Union

logger = logging.getLogger(__name__)

class CoinExAPI:
    """
    Class to interact with CoinEx exchange API using CCXT library
    """
    def __init__(self, api_key: Optional[str] = None, api_secret: Optional[str] = None):
        """
        Initialize the CoinEx API connection
        
        Args:
            api_key: API key for CoinEx
            api_secret: API secret for CoinEx
        """
        self.api_key = api_key or os.environ.get('COINEX_API_KEY', '')
        self.api_secret = api_secret or os.environ.get('COINEX_API_SECRET', '')
        
        # Initialize the CCXT exchange object
        self.exchange = ccxt.coinex({
            'apiKey': self.api_key,
            'secret': self.api_secret,
            'enableRateLimit': True,
        })
        
        self.authenticated = bool(self.api_key and self.api_secret)
        
        # Try to load markets on initialization
        try:
            if self.authenticated:
                self.exchange.load_markets()
                logger.info("Successfully connected to CoinEx API and loaded markets")
            else:
                logger.warning("Initialized without API credentials - limited functionality available")
        except Exception as e:
            logger.error(f"Error connecting to CoinEx API: {str(e)}")
    
    def get_markets(self) -> List[Dict]:
        """
        Get all available markets from CoinEx
        
        Returns:
            List of market dictionaries
        """
        try:
            self.exchange.load_markets()
            markets = []
            for symbol, market in self.exchange.markets.items():
                # Filter for spot markets only
                if market['spot']:
                    markets.append({
                        'symbol': symbol,
                        'base': market['base'],
                        'quote': market['quote'],
                        'active': market['active'],
                        'precision': market['precision'],
                        'limits': market['limits'],
                    })
            return markets
        except Exception as e:
            logger.error(f"Error getting markets: {str(e)}")
            return []
    
    def get_ticker(self, symbol: str) -> Dict:
        """
        Get current ticker for a specific symbol
        
        Args:
            symbol: Trading pair symbol (e.g., 'BTC/USDT')
            
        Returns:
            Ticker information
        """
        try:
            # Convert symbol format if needed to match CoinEx requirements
            # CoinEx uses format like 'BTCUSDT' while CCXT typically expects 'BTC/USDT'
            ccxt_symbol = symbol  # Default to original symbol
            
            if '/' in symbol:
                # Leave as is, CCXT will handle the conversion
                pass
            else:
                # If given without slash (e.g. 'BTCUSDT'), try to convert to CCXT format
                # This is just a fallback, symbols should be stored with slashes
                converted = False
                for common_quote in ['USDT', 'BTC', 'ETH', 'USD']:
                    if symbol.endswith(common_quote):
                        base = symbol[:-len(common_quote)]
                        if base:  # Make sure the base is not empty
                            ccxt_symbol = f"{base}/{common_quote}"
                            converted = True
                            break
                
                if not converted:
                    # If we couldn't parse it, just use as is and let CCXT try
                    logger.warning(f"Could not convert symbol {symbol} to CCXT format, using as is")
            
            logger.info(f"Getting ticker for {symbol} (CCXT format: {ccxt_symbol})")
            return self.exchange.fetch_ticker(ccxt_symbol)
        except Exception as e:
            logger.error(f"Error getting ticker for {symbol}: {str(e)}")
            return {}
    
    def get_balance(self) -> Dict:
        """
        Get account balance
        
        Returns:
            Balance information
        """
        if not self.authenticated:
            logger.error("API credentials required for balance check")
            return {}
            
        try:
            return self.exchange.fetch_balance()
        except Exception as e:
            logger.error(f"Error getting balance: {str(e)}")
            return {}
    
    def get_ohlcv(self, symbol: str, timeframe: str = '1h', limit: int = 100) -> List:
        """
        Get OHLCV (candlestick) data
        
        Args:
            symbol: Trading pair symbol (e.g., 'BTC/USDT')
            timeframe: Timeframe for candles ('1m', '5m', '15m', '1h', '4h', '1d', etc.)
            limit: Number of candles to retrieve
            
        Returns:
            List of OHLCV candles
        """
        try:
            # Convert symbol format if needed to match CoinEx requirements
            # CoinEx uses format like 'BTCUSDT' while CCXT typically expects 'BTC/USDT'
            ccxt_symbol = symbol  # Default to original symbol
            
            if '/' in symbol:
                # Leave as is, CCXT will handle the conversion
                pass
            else:
                # If given without slash (e.g. 'BTCUSDT'), try to convert to CCXT format
                # This is just a fallback, symbols should be stored with slashes
                converted = False
                for common_quote in ['USDT', 'BTC', 'ETH', 'USD']:
                    if symbol.endswith(common_quote):
                        base = symbol[:-len(common_quote)]
                        if base:  # Make sure the base is not empty
                            ccxt_symbol = f"{base}/{common_quote}"
                            converted = True
                            break
                
                if not converted:
                    # If we couldn't parse it, just use as is and let CCXT try
                    logger.warning(f"Could not convert symbol {symbol} to CCXT format, using as is")
            
            logger.info(f"Getting OHLCV for {symbol} (CCXT format: {ccxt_symbol})")
            ohlcv = self.exchange.fetch_ohlcv(ccxt_symbol, timeframe, limit=limit)
            return [
                {
                    'timestamp': candle[0],
                    'datetime': datetime.fromtimestamp(candle[0]/1000).strftime('%Y-%m-%d %H:%M:%S'),
                    'open': candle[1],
                    'high': candle[2],
                    'low': candle[3],
                    'close': candle[4],
                    'volume': candle[5]
                }
                for candle in ohlcv
            ]
        except Exception as e:
            logger.error(f"Error getting OHLCV data for {symbol}: {str(e)}")
            return []
    
    def create_order(self, symbol: str, order_type: str, side: str, 
                     amount: float, price: Optional[float] = None) -> Dict:
        """
        Create a new order
        
        Args:
            symbol: Trading pair symbol (e.g., 'BTC/USDT')
            order_type: Type of order ('limit' or 'market')
            side: Order side ('buy' or 'sell')
            amount: Order amount
            price: Order price (required for limit orders)
            
        Returns:
            Order information
        """
        if not self.authenticated:
            logger.error("API credentials required for creating orders")
            return {}
            
        try:
            return self.exchange.create_order(symbol, order_type, side, amount, price)
        except Exception as e:
            logger.error(f"Error creating order: {str(e)}")
            return {}
    
    def cancel_order(self, order_id: str, symbol: str) -> Dict:
        """
        Cancel an existing order
        
        Args:
            order_id: ID of the order to cancel
            symbol: Trading pair symbol (e.g., 'BTC/USDT')
            
        Returns:
            Result of the cancellation
        """
        if not self.authenticated:
            logger.error("API credentials required for cancelling orders")
            return {}
            
        try:
            return self.exchange.cancel_order(order_id, symbol)
        except Exception as e:
            logger.error(f"Error cancelling order {order_id}: {str(e)}")
            return {}
    
    def get_open_orders(self, symbol: Optional[str] = None) -> List[Dict]:
        """
        Get open orders
        
        Args:
            symbol: Trading pair symbol (optional)
            
        Returns:
            List of open orders
        """
        if not self.authenticated:
            logger.error("API credentials required for getting open orders")
            return []
            
        try:
            return self.exchange.fetch_open_orders(symbol=symbol)
        except Exception as e:
            logger.error(f"Error getting open orders: {str(e)}")
            return []
    
    def get_order_history(self, symbol: Optional[str] = None, limit: int = 50) -> List[Dict]:
        """
        Get order history
        
        Args:
            symbol: Trading pair symbol (optional)
            limit: Maximum number of orders to retrieve
            
        Returns:
            List of historical orders
        """
        if not self.authenticated:
            logger.error("API credentials required for getting order history")
            return []
            
        try:
            return self.exchange.fetch_closed_orders(symbol=symbol, limit=limit)
        except Exception as e:
            logger.error(f"Error getting order history: {str(e)}")
            return []

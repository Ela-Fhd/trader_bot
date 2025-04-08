import os
import time
import logging
import threading
import datetime
from typing import Dict, List, Optional, Tuple

from app import app, db
from models import TradingPair, TradingStrategy, Trade, BotSettings
from coinex_api import CoinExAPI
from trading_strategies import get_strategy_by_name

# Configure logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

class TradingBot:
    """
    The main trading bot engine that processes strategies and executes trades
    """
    def __init__(self):
        """Initialize the trading bot"""
        self.api = None
        self.settings = None
        self.is_running = False
        self.thread = None
        self.last_check_time = {}  # Store last check time for each trading pair
        self.daily_trades = {}  # Store count of daily trades for each trading pair
    
    def initialize(self):
        """Initialize the bot with settings from the database"""
        with app.app_context():
            self.settings = db.session.query(BotSettings).first()
            if not self.settings:
                logger.warning("No settings found in database. Bot cannot start.")
                return False
            
            # Initialize API with stored credentials
            self.api = CoinExAPI(self.settings.api_key, self.settings.api_secret)
            
            # Check if API is properly initialized
            if not self.api.authenticated:
                logger.warning("API authentication failed. Check API credentials.")
                return False
            
            logger.info("Bot initialized successfully with settings from database")
            return True
    
    def start(self):
        """Start the trading bot in a separate thread"""
        if self.is_running:
            logger.warning("Bot is already running")
            return False
        
        if not self.initialize():
            logger.error("Failed to initialize bot")
            return False
        
        self.is_running = True
        self.thread = threading.Thread(target=self._run_bot)
        self.thread.daemon = True
        self.thread.start()
        
        logger.info("Trading bot started")
        return True
    
    def stop(self):
        """Stop the trading bot"""
        if not self.is_running:
            logger.warning("Bot is not running")
            return False
        
        self.is_running = False
        if self.thread:
            self.thread.join(timeout=5.0)
        
        logger.info("Trading bot stopped")
        return True
    
    def _run_bot(self):
        """Main bot loop that runs in a separate thread"""
        while self.is_running:
            try:
                with app.app_context():
                    # Reload settings to get the latest configuration
                    self.settings = db.session.query(BotSettings).first()
                    
                    # If bot is disabled in settings, pause execution
                    if not self.settings or not self.settings.is_active:
                        logger.info("Bot is disabled in settings. Pausing execution.")
                        time.sleep(30)  # Check again after 30 seconds
                        continue
                    
                    # Process active strategies
                    self._process_strategies()
                    
            except Exception as e:
                logger.error(f"Error in bot main loop: {str(e)}")
            
            # Sleep before the next iteration
            time.sleep(60)  # Run every minute
    
    def _process_strategies(self):
        """Process all active trading strategies"""
        # Reset daily trades counter if it's a new day
        self._reset_daily_trades_if_needed()
        
        # Get all active strategies
        active_strategies = db.session.query(TradingStrategy).filter_by(is_active=True).all()
        
        if not active_strategies:
            logger.info("No active strategies found")
            return
        
        logger.info(f"Processing {len(active_strategies)} active strategies")
        
        for strategy in active_strategies:
            try:
                # Get the trading pair for this strategy
                trading_pair = db.session.query(TradingPair).get(strategy.trading_pair_id)
                
                if not trading_pair or not trading_pair.is_active:
                    logger.warning(f"Strategy {strategy.id} skipped - trading pair inactive or not found")
                    continue
                
                # Check if we've exceeded daily trade limit for this pair
                pair_key = f"{trading_pair.id}_{datetime.date.today().isoformat()}"
                if self.daily_trades.get(pair_key, 0) >= self.settings.max_daily_trades:
                    logger.info(f"Daily trade limit reached for {trading_pair.symbol}")
                    continue
                
                # Check if enough time has passed since the last check for this pair
                pair_time_key = f"{trading_pair.id}_last_check"
                last_check = self.last_check_time.get(pair_time_key, 0)
                current_time = time.time()
                
                # Only check each pair every 5 minutes to avoid excessive API calls
                if current_time - last_check < 300:  # 5 minutes in seconds
                    continue
                
                self.last_check_time[pair_time_key] = current_time
                
                # Get market data for the trading pair
                ohlcv_data = self.api.get_ohlcv(trading_pair.symbol, timeframe='1h', limit=100)
                
                if not ohlcv_data:
                    logger.warning(f"No OHLCV data available for {trading_pair.symbol}")
                    continue
                
                # Create the strategy instance
                strategy_instance = get_strategy_by_name(strategy.strategy_type, strategy.parameters)
                
                if not strategy_instance:
                    logger.error(f"Failed to create strategy instance for {strategy.name}")
                    continue
                
                # Get the trading signal
                signal = strategy_instance.get_signal(ohlcv_data)
                
                logger.info(f"Strategy {strategy.name} ({trading_pair.symbol}): Signal = {signal}")
                
                # Execute trades based on the signal
                if signal in ['BUY', 'SELL']:
                    self._execute_trade(strategy, trading_pair, signal, ohlcv_data[-1]['close'])
            
            except Exception as e:
                logger.error(f"Error processing strategy {strategy.id}: {str(e)}")
    
    def _execute_trade(self, strategy, trading_pair, signal, current_price):
        """Execute a trade based on the strategy signal"""
        # Check if we've exceeded daily trade limit
        pair_key = f"{trading_pair.id}_{datetime.date.today().isoformat()}"
        
        if self.daily_trades.get(pair_key, 0) >= self.settings.max_daily_trades:
            logger.info(f"Daily trade limit reached for {trading_pair.symbol}")
            return
        
        try:
            # Calculate trade amount based on settings
            # For simplicity, we'll use a fixed percentage of max_trade_size
            # In a real implementation, this would be more sophisticated
            
            # Get account balance first
            balance = self.api.get_balance()
            
            if not balance:
                logger.error("Failed to get account balance")
                return
            
            # For BUY orders, check quote currency balance (e.g., USDT)
            # For SELL orders, check base currency balance (e.g., BTC)
            
            if signal == 'BUY':
                currency = trading_pair.quote_currency
                if currency not in balance:
                    logger.warning(f"No {currency} balance available for buying")
                    return
                
                available_balance = float(balance[currency]['free'])
                trade_value = min(available_balance * 0.1, self.settings.max_trade_size)
                trade_amount = trade_value / current_price
                
            else:  # SELL
                currency = trading_pair.base_currency
                if currency not in balance:
                    logger.warning(f"No {currency} balance available for selling")
                    return
                
                available_balance = float(balance[currency]['free'])
                trade_amount = min(available_balance * 0.1, self.settings.max_trade_size / current_price)
            
            if trade_amount <= 0:
                logger.warning(f"Calculated trade amount is zero or negative: {trade_amount}")
                return
            
            # Create order
            order_type = 'market'  # Use market orders for simplicity
            order = self.api.create_order(
                symbol=trading_pair.symbol,
                order_type=order_type,
                side=signal.lower(),  # API expects lowercase 'buy' or 'sell'
                amount=trade_amount,
                price=None  # Price is not used for market orders
            )
            
            if not order:
                logger.error(f"Failed to create {signal} order for {trading_pair.symbol}")
                return
            
            # Record the trade in the database
            trade = Trade(
                order_id=order.get('id', ''),
                trading_pair_id=trading_pair.id,
                strategy_id=strategy.id,
                order_type=signal,
                price=float(order.get('price', current_price)),
                amount=float(order.get('amount', trade_amount)),
                fee=float(order.get('fee', {}).get('cost', 0.0)),
                status='FILLED' if order.get('status') == 'closed' else 'OPEN'
            )
            
            db.session.add(trade)
            db.session.commit()
            
            # Update daily trades counter
            self.daily_trades[pair_key] = self.daily_trades.get(pair_key, 0) + 1
            
            logger.info(f"Successfully executed {signal} order for {trading_pair.symbol}")
            
        except Exception as e:
            logger.error(f"Error executing trade: {str(e)}")
    
    def _reset_daily_trades_if_needed(self):
        """Reset daily trades counter if it's a new day"""
        today = datetime.date.today().isoformat()
        
        # Filter keys that don't contain today's date
        keys_to_remove = [k for k in self.daily_trades.keys() if today not in k]
        
        # Remove old entries
        for key in keys_to_remove:
            del self.daily_trades[key]


# Create a global bot instance
trading_bot = TradingBot()

def start_bot():
    """Start the trading bot"""
    return trading_bot.start()

def stop_bot():
    """Stop the trading bot"""
    return trading_bot.stop()

def is_bot_running():
    """Check if the bot is running"""
    return trading_bot.is_running

# Start the bot when the module is imported
if __name__ == "__main__":
    # This allows running the bot directly for testing
    logger.info("Starting trading bot in standalone mode")
    start_bot()
    
    try:
        # Keep the main thread alive
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("Keyboard interrupt received, shutting down")
        stop_bot()

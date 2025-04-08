import datetime
from app import db


class TradingPair(db.Model):
    """Model for storing cryptocurrency trading pairs"""
    id = db.Column(db.Integer, primary_key=True)
    symbol = db.Column(db.String(20), nullable=False, unique=True)
    base_currency = db.Column(db.String(10), nullable=False)
    quote_currency = db.Column(db.String(10), nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.datetime.now)
    
    def __repr__(self):
        return f"<TradingPair {self.symbol}>"


class TradingStrategy(db.Model):
    """Model for storing trading strategies"""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    strategy_type = db.Column(db.String(50), nullable=False)  # e.g., 'MA_CROSSOVER', 'RSI_OVERSOLD', etc.
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.datetime.now, onupdate=datetime.datetime.now)
    
    # Strategy parameters stored as JSON
    parameters = db.Column(db.JSON, nullable=False)
    
    # Relationships
    trading_pair_id = db.Column(db.Integer, db.ForeignKey('trading_pair.id'), nullable=False)
    trading_pair = db.relationship('TradingPair', backref=db.backref('strategies', lazy=True))
    
    def __repr__(self):
        return f"<TradingStrategy {self.name}>"


class Trade(db.Model):
    """Model for storing trade records"""
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.String(50), nullable=True)  # Exchange order ID
    trading_pair_id = db.Column(db.Integer, db.ForeignKey('trading_pair.id'), nullable=False)
    strategy_id = db.Column(db.Integer, db.ForeignKey('trading_strategy.id'), nullable=False)
    order_type = db.Column(db.String(20), nullable=False)  # 'BUY' or 'SELL'
    price = db.Column(db.Float, nullable=False)
    amount = db.Column(db.Float, nullable=False)
    fee = db.Column(db.Float, default=0.0)
    status = db.Column(db.String(20), nullable=False)  # 'OPEN', 'FILLED', 'CANCELLED', etc.
    created_at = db.Column(db.DateTime, default=datetime.datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.datetime.now, onupdate=datetime.datetime.now)
    
    # Relationships
    trading_pair = db.relationship('TradingPair', backref=db.backref('trades', lazy=True))
    strategy = db.relationship('TradingStrategy', backref=db.backref('trades', lazy=True))
    
    def __repr__(self):
        return f"<Trade {self.order_type} {self.amount} {self.trading_pair.symbol} @ {self.price}>"


class BotSettings(db.Model):
    """Model for storing bot settings"""
    id = db.Column(db.Integer, primary_key=True)
    api_key = db.Column(db.String(256))
    api_secret = db.Column(db.String(256))
    max_daily_trades = db.Column(db.Integer, default=10)
    max_trade_size = db.Column(db.Float, default=0.01)  # In BTC or equivalent
    risk_level = db.Column(db.String(20), default='MEDIUM')  # 'LOW', 'MEDIUM', 'HIGH'
    is_active = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.datetime.now, onupdate=datetime.datetime.now)
    
    def __repr__(self):
        return f"<BotSettings id={self.id}>"

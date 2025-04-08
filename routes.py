import os
import json
import logging
import datetime
from flask import render_template, request, redirect, url_for, flash, jsonify, session
from sqlalchemy.exc import SQLAlchemyError

from app import app, db
from models import TradingPair, TradingStrategy, Trade, BotSettings
from coinex_api import CoinExAPI
from trading_strategies import get_strategy_by_name, get_available_strategies

# Configure logging
logger = logging.getLogger(__name__)

# Initialize CoinEx API
coinex_api = CoinExAPI()

@app.route('/')
def index():
    """Render the dashboard page"""
    # Get basic stats
    stats = {
        'active_pairs': db.session.query(TradingPair).filter_by(is_active=True).count(),
        'active_strategies': db.session.query(TradingStrategy).filter_by(is_active=True).count(),
        'total_trades': db.session.query(Trade).count(),
        'recent_trades': db.session.query(Trade).order_by(Trade.created_at.desc()).limit(5).all()
    }
    
    # Get bot status
    bot_settings = db.session.query(BotSettings).first()
    bot_active = bot_settings.is_active if bot_settings else False
    
    return render_template('index.html', 
                          stats=stats, 
                          bot_active=bot_active,
                          page='dashboard')

@app.route('/market_status')
def market_status():
    """Render the market status page"""
    # Get all active trading pairs
    trading_pairs = db.session.query(TradingPair).filter_by(is_active=True).all()
    
    # Ensure we have trading pairs in the database
    if not trading_pairs:
        # Add default trading pairs with USDT as quote currency
        default_pairs = [
            {'symbol': 'BTC/USDT', 'base': 'BTC', 'quote': 'USDT'},
            {'symbol': 'ETH/USDT', 'base': 'ETH', 'quote': 'USDT'},
            {'symbol': 'XRP/USDT', 'base': 'XRP', 'quote': 'USDT'},
            {'symbol': 'SOL/USDT', 'base': 'SOL', 'quote': 'USDT'},
            {'symbol': 'DOGE/USDT', 'base': 'DOGE', 'quote': 'USDT'}
        ]
        
        for pair_info in default_pairs:
            new_pair = TradingPair(
                symbol=pair_info['symbol'],
                base_currency=pair_info['base'],
                quote_currency=pair_info['quote'],
                is_active=True
            )
            db.session.add(new_pair)
        
        try:
            db.session.commit()
            trading_pairs = db.session.query(TradingPair).filter_by(is_active=True).all()
        except SQLAlchemyError as e:
            db.session.rollback()
            logger.error(f"Error adding default trading pairs: {str(e)}")
    
    # Get market data for each pair
    market_data = []
    featured_pairs = {
        'BTC/USDT': {'price': None, 'change': None},
        'ETH/USDT': {'price': None, 'change': None},
        'XRP/USDT': {'price': None, 'change': None},
        'SOL/USDT': {'price': None, 'change': None}
    }
    
    for pair in trading_pairs:
        ticker = coinex_api.get_ticker(pair.symbol)
        if ticker:
            logger.debug(f"Ticker data for {pair.symbol}: {ticker}")
            
            # Calculate 24h change percentage
            change_pct = 'N/A'
            last_price = ticker.get('last', 'N/A')
            open_price = ticker.get('open', None)
            
            if isinstance(last_price, (int, float)) and isinstance(open_price, (int, float)) and open_price > 0:
                change_pct = ((last_price - open_price) / open_price) * 100
            
            data = {
                'symbol': pair.symbol,
                'last_price': last_price,
                'change_24h': change_pct,
                'high_24h': ticker.get('high', 'N/A'),
                'low_24h': ticker.get('low', 'N/A'),
                'volume_24h': ticker.get('volume', 'N/A'),
            }
            
            market_data.append(data)
            
            # Update featured pairs data if this is one of the featured pairs
            if pair.symbol in featured_pairs:
                featured_pairs[pair.symbol]['price'] = last_price
                featured_pairs[pair.symbol]['change'] = change_pct
    
    return render_template('market_status.html', 
                          market_data=market_data,
                          featured_pairs=featured_pairs,
                          page='market_status')

@app.route('/strategy', methods=['GET', 'POST'])
def strategy():
    """Render the strategy configuration page"""
    # Get available trading pairs
    trading_pairs = db.session.query(TradingPair).all()
    
    # Get available strategies
    available_strategies = get_available_strategies()
    
    # Get existing strategies
    existing_strategies = db.session.query(TradingStrategy).all()
    
    if request.method == 'POST':
        try:
            # Get form data
            name = request.form.get('name')
            description = request.form.get('description', '')
            strategy_type = request.form.get('strategy_type')
            trading_pair_id = request.form.get('trading_pair_id')
            is_active = request.form.get('is_active') == 'on'
            
            # Get strategy parameters
            parameters = {}
            for strategy_info in available_strategies:
                if strategy_info['id'] == strategy_type:
                    for param_name, param_info in strategy_info['parameters'].items():
                        param_value = request.form.get(param_name)
                        if param_info['type'] == 'int':
                            parameters[param_name] = int(param_value) if param_value else param_info['default']
                        elif param_info['type'] == 'float':
                            parameters[param_name] = float(param_value) if param_value else param_info['default']
                        elif param_info['type'] == 'bool':
                            parameters[param_name] = param_value == 'on'
                        else:
                            parameters[param_name] = param_value or param_info['default']
            
            # Create new strategy
            new_strategy = TradingStrategy(
                name=name,
                description=description,
                strategy_type=strategy_type,
                trading_pair_id=trading_pair_id,
                is_active=is_active,
                parameters=parameters
            )
            
            db.session.add(new_strategy)
            db.session.commit()
            
            flash('Strategy has been created successfully!', 'success')
            return redirect(url_for('strategy'))
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error creating strategy: {str(e)}")
            flash(f'Error creating strategy: {str(e)}', 'danger')
    
    return render_template('strategy.html', 
                          trading_pairs=trading_pairs,
                          available_strategies=available_strategies,
                          existing_strategies=existing_strategies,
                          page='strategy')

@app.route('/strategy/<int:strategy_id>/toggle', methods=['POST'])
def toggle_strategy(strategy_id):
    """Toggle strategy active status"""
    try:
        strategy = db.session.query(TradingStrategy).get(strategy_id)
        if strategy:
            strategy.is_active = not strategy.is_active
            db.session.commit()
            return jsonify({'success': True, 'is_active': strategy.is_active})
        else:
            return jsonify({'success': False, 'error': 'Strategy not found'}), 404
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error toggling strategy: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/strategy/<int:strategy_id>/delete', methods=['POST'])
def delete_strategy(strategy_id):
    """Delete a strategy"""
    try:
        strategy = db.session.query(TradingStrategy).get(strategy_id)
        if strategy:
            db.session.delete(strategy)
            db.session.commit()
            flash('Strategy has been deleted successfully!', 'success')
        else:
            flash('Strategy not found!', 'danger')
        return redirect(url_for('strategy'))
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error deleting strategy: {str(e)}")
        flash(f'Error deleting strategy: {str(e)}', 'danger')
        return redirect(url_for('strategy'))

@app.route('/trade_history')
def trade_history():
    """Render the trade history page"""
    # Get trade history with related objects
    trades = db.session.query(Trade).order_by(Trade.created_at.desc()).all()
    
    return render_template('trade_history.html', 
                          trades=trades,
                          page='trade_history')

@app.route('/settings', methods=['GET', 'POST'])
def settings():
    """Render the settings page"""
    # Get current settings
    settings = db.session.query(BotSettings).first()
    if not settings:
        settings = BotSettings()
        db.session.add(settings)
        db.session.commit()
    
    if request.method == 'POST':
        try:
            # Update settings
            settings.api_key = request.form.get('api_key', '')
            settings.api_secret = request.form.get('api_secret', '')
            settings.max_daily_trades = int(request.form.get('max_daily_trades', 10))
            settings.max_trade_size = float(request.form.get('max_trade_size', 0.01))
            settings.risk_level = request.form.get('risk_level', 'MEDIUM')
            
            db.session.commit()
            
            # Update API client with new credentials
            global coinex_api
            coinex_api = CoinExAPI(settings.api_key, settings.api_secret)
            
            flash('Settings have been updated successfully!', 'success')
            return redirect(url_for('settings'))
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error updating settings: {str(e)}")
            flash(f'Error updating settings: {str(e)}', 'danger')
    
    return render_template('settings.html', 
                          settings=settings,
                          page='settings')

@app.route('/settings/toggle_bot', methods=['POST'])
def toggle_bot():
    """Toggle bot active status"""
    try:
        settings = db.session.query(BotSettings).first()
        if settings:
            settings.is_active = not settings.is_active
            db.session.commit()
            return jsonify({'success': True, 'is_active': settings.is_active})
        else:
            return jsonify({'success': False, 'error': 'Settings not found'}), 404
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error toggling bot: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/trading_pairs', methods=['GET', 'POST'])
def trading_pairs():
    """Manage trading pairs"""
    if request.method == 'POST':
        try:
            # Add new trading pair
            symbol = request.form.get('symbol')
            base_currency = request.form.get('base_currency')
            quote_currency = request.form.get('quote_currency')
            
            # Ensure quote currency is USDT
            if quote_currency != 'USDT':
                flash('فقط جفت ارزهای با ارز پایه USDT قابل استفاده هستند!', 'warning')
                return redirect(url_for('trading_pairs'))
            
            # Check if pair already exists
            existing_pair = db.session.query(TradingPair).filter_by(symbol=symbol).first()
            if existing_pair:
                flash('این جفت ارز قبلاً اضافه شده است!', 'warning')
            else:
                new_pair = TradingPair(
                    symbol=symbol,
                    base_currency=base_currency,
                    quote_currency=quote_currency,
                    is_active=True
                )
                db.session.add(new_pair)
                db.session.commit()
                flash('جفت ارز با موفقیت اضافه شد!', 'success')
            
            return redirect(url_for('trading_pairs'))
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error adding trading pair: {str(e)}")
            flash(f'خطا در اضافه کردن جفت ارز: {str(e)}', 'danger')
    
    # Get available markets from CoinEx
    all_markets = coinex_api.get_markets()
    
    # Filter markets to only include pairs with USDT
    markets = []
    for market in all_markets:
        market_name = market.get('market', '')
        # Check if market ends with USDT
        if market_name.endswith('USDT'):
            # Format market for display
            base = market_name[:-4]  # Remove 'USDT' from the end
            if base:  # Ensure base is not empty
                markets.append({
                    'symbol': f"{base}/USDT",
                    'market': market_name,
                    'base_currency': base,
                    'quote_currency': 'USDT'
                })
    
    # Get existing pairs
    existing_pairs = db.session.query(TradingPair).all()
    
    return render_template('trading_pairs.html', 
                          markets=markets,
                          existing_pairs=existing_pairs,
                          page='trading_pairs')

@app.route('/trading_pairs/<int:pair_id>/toggle', methods=['POST'])
def toggle_trading_pair(pair_id):
    """Toggle trading pair active status"""
    try:
        pair = db.session.query(TradingPair).get(pair_id)
        if pair:
            pair.is_active = not pair.is_active
            db.session.commit()
            return jsonify({'success': True, 'is_active': pair.is_active})
        else:
            return jsonify({'success': False, 'error': 'Trading pair not found'}), 404
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error toggling trading pair: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/market_data/<symbol>')
def get_market_data(symbol):
    """API endpoint to get market data for a specific symbol"""
    try:
        # Get OHLCV data
        timeframe = request.args.get('timeframe', '1h')
        limit = int(request.args.get('limit', 100))
        
        ohlcv_data = coinex_api.get_ohlcv(symbol, timeframe, limit)
        
        return jsonify({
            'success': True,
            'data': ohlcv_data
        })
    except Exception as e:
        logger.error(f"Error getting market data: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500
        
@app.route('/api/live_prices')
def get_live_prices():
    """API endpoint to get live prices for all active trading pairs"""
    try:
        # Get all active trading pairs
        trading_pairs = db.session.query(TradingPair).filter_by(is_active=True).all()
        
        # Get latest price data for each pair
        price_data = {}
        for pair in trading_pairs:
            ticker = coinex_api.get_ticker(pair.symbol)
            if ticker:
                # Calculate 24h change percentage
                change_pct = 'N/A'
                last_price = ticker.get('last', 'N/A')
                open_price = ticker.get('open', None)
                
                if isinstance(last_price, (int, float)) and isinstance(open_price, (int, float)) and open_price > 0:
                    change_pct = ((last_price - open_price) / open_price) * 100
                
                price_data[pair.symbol] = {
                    'price': last_price,
                    'change': change_pct,
                    'high': ticker.get('high', 'N/A'),
                    'low': ticker.get('low', 'N/A'),
                    'volume': ticker.get('volume', 'N/A')
                }
        
        return jsonify({
            'success': True,
            'data': price_data,
            'timestamp': datetime.datetime.now().isoformat()
        })
    except Exception as e:
        logger.error(f"Error getting live prices: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/analyze_strategy/<int:strategy_id>')
def analyze_strategy(strategy_id):
    """API endpoint to analyze a strategy with current market data"""
    try:
        # Get strategy
        strategy_obj = db.session.query(TradingStrategy).get(strategy_id)
        if not strategy_obj:
            return jsonify({'success': False, 'error': 'Strategy not found'}), 404
        
        # Get trading pair
        trading_pair = db.session.query(TradingPair).get(strategy_obj.trading_pair_id)
        if not trading_pair:
            return jsonify({'success': False, 'error': 'Trading pair not found'}), 404
        
        # Get OHLCV data
        timeframe = request.args.get('timeframe', '1h')
        limit = int(request.args.get('limit', 100))
        
        ohlcv_data = coinex_api.get_ohlcv(trading_pair.symbol, timeframe, limit)
        
        # Create strategy instance
        strategy_instance = get_strategy_by_name(strategy_obj.strategy_type, strategy_obj.parameters)
        if not strategy_instance:
            return jsonify({'success': False, 'error': 'Failed to create strategy instance'}), 500
        
        # Analyze
        result = strategy_instance.analyze(ohlcv_data)
        
        # Add some additional info
        result['strategy_name'] = strategy_obj.name
        result['trading_pair'] = trading_pair.symbol
        result['timeframe'] = timeframe
        
        return jsonify({
            'success': True,
            'data': result
        })
    except Exception as e:
        logger.error(f"Error analyzing strategy: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

# Error handlers
@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@app.errorhandler(500)
def server_error(e):
    return render_template('500.html'), 500

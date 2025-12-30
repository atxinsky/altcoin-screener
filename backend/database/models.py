from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, JSON, Index
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()


class KlineData(Base):
    """K-line candlestick data"""
    __tablename__ = "klines"

    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String, index=True, nullable=False)
    timeframe = Column(String, index=True, nullable=False)
    timestamp = Column(DateTime, index=True, nullable=False)
    open = Column(Float, nullable=False)
    high = Column(Float, nullable=False)
    low = Column(Float, nullable=False)
    close = Column(Float, nullable=False)
    volume = Column(Float, nullable=False)
    quote_volume = Column(Float, nullable=False)
    trades = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index('idx_symbol_timeframe_timestamp', 'symbol', 'timeframe', 'timestamp', unique=True),
    )


class TechnicalIndicators(Base):
    """Technical indicators for each symbol"""
    __tablename__ = "indicators"

    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String, index=True, nullable=False)
    timeframe = Column(String, index=True, nullable=False)
    timestamp = Column(DateTime, index=True, nullable=False)

    # Moving Averages
    sma_20 = Column(Float)
    sma_50 = Column(Float)
    sma_200 = Column(Float)
    ema_7 = Column(Float)
    ema_14 = Column(Float)
    ema_30 = Column(Float)
    ema_52 = Column(Float)

    # MACD
    macd = Column(Float)
    macd_signal = Column(Float)
    macd_histogram = Column(Float)
    macd_golden_cross = Column(Boolean, default=False)

    # RSI
    rsi = Column(Float)

    # Bollinger Bands
    bb_upper = Column(Float)
    bb_middle = Column(Float)
    bb_lower = Column(Float)

    # Volume
    volume_sma_20 = Column(Float)

    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index('idx_ind_symbol_timeframe_timestamp', 'symbol', 'timeframe', 'timestamp'),
    )


class ScreeningResult(Base):
    """Screening results for altcoins"""
    __tablename__ = "screening_results"

    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String, index=True, nullable=False)
    timestamp = Column(DateTime, index=True, nullable=False)
    timeframe = Column(String, nullable=False)

    # Price ratios
    price_btc_ratio = Column(Float)
    price_eth_ratio = Column(Float)
    btc_ratio_change_pct = Column(Float)
    eth_ratio_change_pct = Column(Float)

    # Scoring
    beta_score = Column(Float)
    volume_score = Column(Float)
    technical_score = Column(Float)
    total_score = Column(Float)

    # Conditions
    above_sma = Column(Boolean, default=False)
    macd_golden_cross = Column(Boolean, default=False)
    above_all_ema = Column(Boolean, default=False)
    volume_surge = Column(Boolean, default=False)
    price_anomaly = Column(Boolean, default=False)

    # Price change
    price_change_5m = Column(Float)
    price_change_15m = Column(Float)
    price_change_1h = Column(Float)
    price_change_4h = Column(Float)

    # Volume
    volume_24h = Column(Float)
    volume_change_pct = Column(Float)

    # Additional data
    current_price = Column(Float)
    extra_data = Column(JSON)

    notified = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index('idx_screen_timestamp', 'timestamp', 'total_score'),
    )


class Order(Base):
    """Trading orders"""
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String, index=True, nullable=False)
    side = Column(String, nullable=False)  # BUY or SELL
    order_type = Column(String, nullable=False)  # MARKET or LIMIT
    quantity = Column(Float, nullable=False)
    price = Column(Float)  # For limit orders
    stop_price = Column(Float)  # For stop orders

    # Order status
    status = Column(String, default='PENDING')  # PENDING, FILLED, CANCELLED, FAILED
    exchange_order_id = Column(String)  # Binance order ID

    # Execution details
    filled_quantity = Column(Float, default=0)
    avg_fill_price = Column(Float)
    commission = Column(Float)
    commission_asset = Column(String)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, onupdate=datetime.utcnow)
    executed_at = Column(DateTime)

    # Metadata
    notes = Column(String)

    __table_args__ = (
        Index('idx_order_symbol_status', 'symbol', 'status'),
        Index('idx_order_created_at', 'created_at'),
    )


class Watchlist(Base):
    """User watchlist / favorite symbols"""
    __tablename__ = "watchlist"

    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String, unique=True, index=True, nullable=False)
    added_at = Column(DateTime, default=datetime.utcnow)
    notes = Column(String)


class Alert(Base):
    """Alert history"""
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String, index=True, nullable=False)
    alert_type = Column(String, nullable=False)
    timeframe = Column(String)
    message = Column(String, nullable=False)
    data = Column(JSON)
    sent_via = Column(String)  # email, telegram, both
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)


class ImportedTrade(Base):
    """Imported trading data from CSV files"""
    __tablename__ = "imported_trades"

    id = Column(Integer, primary_key=True, index=True)
    import_id = Column(String, index=True, nullable=False)  # Batch import identifier
    trade_id = Column(String, index=True)  # Original trade ID from exchange
    symbol = Column(String, index=True, nullable=False)
    side = Column(String, nullable=False)  # BUY or SELL
    price = Column(Float, nullable=False)
    quantity = Column(Float, nullable=False)
    quote_quantity = Column(Float, nullable=False)  # Total value in quote currency
    commission = Column(Float)
    commission_asset = Column(String)
    timestamp = Column(DateTime, index=True, nullable=False)
    is_buyer = Column(Boolean)
    is_maker = Column(Boolean)
    raw_data = Column(JSON)  # Store original CSV row
    imported_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index('idx_import_symbol_timestamp', 'import_id', 'symbol', 'timestamp'),
    )


class BacktestAnalysis(Base):
    """Backtest analysis results"""
    __tablename__ = "backtest_analysis"

    id = Column(Integer, primary_key=True, index=True)
    analysis_id = Column(String, index=True, nullable=False, unique=True)  # Unique identifier for this analysis
    import_id = Column(String, index=True, nullable=False)  # Link to imported trades
    symbol = Column(String, index=True)  # Specific symbol analyzed, null for overall
    timeframe = Column(String)  # Analysis timeframe

    # Overall statistics
    total_trades = Column(Integer)
    winning_trades = Column(Integer)
    losing_trades = Column(Integer)
    win_rate = Column(Float)

    # P&L metrics
    total_pnl = Column(Float)
    total_pnl_percentage = Column(Float)
    avg_win = Column(Float)
    avg_loss = Column(Float)
    profit_factor = Column(Float)

    # Risk metrics
    max_drawdown = Column(Float)
    max_drawdown_percentage = Column(Float)
    sharpe_ratio = Column(Float)

    # Trading behavior
    avg_holding_time_hours = Column(Float)
    total_commission = Column(Float)

    # Additional analysis data
    analysis_data = Column(JSON)  # Store detailed charts, distributions, etc.
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    __table_args__ = (
        Index('idx_analysis_import_symbol', 'import_id', 'symbol'),
    )


class ImportHistory(Base):
    """Track CSV import history"""
    __tablename__ = "import_history"

    id = Column(Integer, primary_key=True, index=True)
    import_id = Column(String, index=True, nullable=False, unique=True)
    filename = Column(String, nullable=False)
    file_hash = Column(String)  # MD5 hash to detect duplicate imports
    rows_imported = Column(Integer)
    date_range_start = Column(DateTime)
    date_range_end = Column(DateTime)
    symbols_count = Column(Integer)
    import_notes = Column(String)
    imported_at = Column(DateTime, default=datetime.utcnow, index=True)


class SimAccount(Base):
    """Simulated trading account"""
    __tablename__ = "sim_accounts"

    id = Column(Integer, primary_key=True, index=True)
    account_name = Column(String, index=True, nullable=False)
    initial_balance = Column(Float, nullable=False, default=10000.0)
    current_balance = Column(Float, nullable=False)  # Available balance
    frozen_balance = Column(Float, default=0.0)  # Balance in open positions
    total_equity = Column(Float, nullable=False)  # current_balance + position value

    # Trading statistics
    total_trades = Column(Integer, default=0)
    winning_trades = Column(Integer, default=0)
    losing_trades = Column(Integer, default=0)
    total_pnl = Column(Float, default=0.0)
    total_commission = Column(Float, default=0.0)

    # Auto trading settings
    auto_trading_enabled = Column(Boolean, default=False)
    max_positions = Column(Integer, default=5)
    position_size_pct = Column(Float, default=2.0)  # % of total equity per position

    # Strategy config - basic
    entry_score_min = Column(Float, default=75.0)
    entry_technical_min = Column(Float, default=60.0)
    stop_loss_pct = Column(Float, default=3.0)
    take_profit_levels = Column(JSON, default=[6.0, 10.0, 15.0])  # Multiple TP levels

    # Strategy config - advanced (JSON for flexibility)
    strategy_config = Column(JSON, default={
        'require_macd_golden': True,
        'require_volume_surge': False,
        'trailing_stop_enabled': False,
        'trailing_stop_pct': 2.0,
        'max_holding_hours': 24
    })

    # Status
    is_active = Column(Boolean, default=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        Index('idx_simaccount_active', 'is_active', 'auto_trading_enabled'),
    )


class SimPosition(Base):
    """Simulated open positions"""
    __tablename__ = "sim_positions"

    id = Column(Integer, primary_key=True, index=True)
    account_id = Column(Integer, index=True, nullable=False)  # FK to sim_accounts
    symbol = Column(String, index=True, nullable=False)

    # Entry details
    entry_price = Column(Float, nullable=False)
    entry_time = Column(DateTime, nullable=False, index=True)
    quantity = Column(Float, nullable=False)
    entry_value = Column(Float, nullable=False)  # Total value at entry
    entry_score = Column(Float)  # Screening score at entry

    # Current status
    current_price = Column(Float)
    current_value = Column(Float)
    unrealized_pnl = Column(Float, default=0.0)
    unrealized_pnl_pct = Column(Float, default=0.0)

    # Stop loss / Take profit
    stop_loss_price = Column(Float)
    take_profit_prices = Column(JSON)  # List of TP prices
    remaining_quantity = Column(Float, nullable=False)  # For partial exits

    # Exit tracking
    partial_exits = Column(JSON, default=[])  # List of {price, quantity, time}
    is_closed = Column(Boolean, default=False, index=True)
    close_time = Column(DateTime)
    close_reason = Column(String)  # 'STOP_LOSS', 'TAKE_PROFIT', 'MANUAL', 'TIME_STOP'

    # Metadata
    entry_signals = Column(JSON)  # Store entry signals for analysis
    notes = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        Index('idx_simposition_account_symbol', 'account_id', 'symbol', 'is_closed'),
    )


class SimTrade(Base):
    """Simulated trade history"""
    __tablename__ = "sim_trades"

    id = Column(Integer, primary_key=True, index=True)
    account_id = Column(Integer, index=True, nullable=False)
    position_id = Column(Integer, index=True)  # Link to position
    symbol = Column(String, index=True, nullable=False)

    # Trade details
    side = Column(String, nullable=False)  # 'BUY' or 'SELL'
    price = Column(Float, nullable=False)
    quantity = Column(Float, nullable=False)
    value = Column(Float, nullable=False)  # price * quantity
    commission = Column(Float, default=0.0)
    commission_asset = Column(String, default='USDT')

    # P&L (for closing trades)
    pnl = Column(Float)
    pnl_pct = Column(Float)

    # Context
    trade_type = Column(String)  # 'ENTRY', 'PARTIAL_EXIT', 'FULL_EXIT'
    exit_reason = Column(String)  # 'STOP_LOSS', 'TAKE_PROFIT_1', 'TAKE_PROFIT_2', etc.

    # Signals and scores
    entry_score = Column(Float)
    signals = Column(JSON)  # Entry/exit signals

    # Timestamps
    trade_time = Column(DateTime, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Metadata
    notes = Column(String)

    __table_args__ = (
        Index('idx_simtrade_account_time', 'account_id', 'trade_time'),
        Index('idx_simtrade_symbol_time', 'symbol', 'trade_time'),
    )


class NotificationSettings(Base):
    """Notification settings for email and telegram"""
    __tablename__ = "notification_settings"

    id = Column(Integer, primary_key=True, index=True)

    # 通知开关
    email_enabled = Column(Boolean, default=True)
    telegram_enabled = Column(Boolean, default=True)

    # 频率控制（分钟）
    min_interval_minutes = Column(Integer, default=30)  # 最小通知间隔
    last_notification_time = Column(DateTime)  # 上次发送时间

    # 每日通知限制
    daily_limit = Column(Integer, default=10)  # 每天最多发送次数
    daily_count = Column(Integer, default=0)  # 今日已发送次数
    daily_count_reset_date = Column(String)  # 重置日期 (YYYY-MM-DD)

    # 通知内容设置
    min_score_threshold = Column(Float, default=75.0)  # 最低分数阈值
    notify_top_n = Column(Integer, default=5)  # 每次通知前N个

    # 通知类型
    notify_high_score = Column(Boolean, default=True)  # 高分机会通知
    notify_new_signals = Column(Boolean, default=True)  # 新信号通知
    notify_position_updates = Column(Boolean, default=True)  # 持仓更新通知

    # 静默时段（北京时间）
    quiet_hours_enabled = Column(Boolean, default=True)
    quiet_hours_start = Column(Integer, default=22)  # 22:00 开始静默
    quiet_hours_end = Column(Integer, default=7)  # 07:00 结束静默

    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class AutoTradingLog(Base):
    """Log for auto trading decisions"""
    __tablename__ = "auto_trading_logs"

    id = Column(Integer, primary_key=True, index=True)
    account_id = Column(Integer, index=True, nullable=False)

    # Decision details
    action = Column(String, nullable=False)  # 'OPEN_POSITION', 'CLOSE_POSITION', 'SKIP', 'ERROR'
    symbol = Column(String, index=True)
    reason = Column(String, nullable=False)

    # Context
    screening_score = Column(Float)
    screening_data = Column(JSON)  # Store screening result for analysis

    # Result
    success = Column(Boolean, default=False)
    error_message = Column(String)

    # Timestamp
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)

    __table_args__ = (
        Index('idx_autolog_account_timestamp', 'account_id', 'timestamp'),
    )

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

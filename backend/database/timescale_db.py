"""
TimescaleDB Connection Module
用于存储和查询时序数据（K线数据）
"""

import os
import logging
from contextlib import contextmanager
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import QueuePool

logger = logging.getLogger(__name__)

# Get TimescaleDB URL from environment
TIMESCALE_URL = os.getenv('TIMESCALE_URL', 'postgresql://postgres:ledger123@localhost:5432/altcoin_screener')

# Create engine with connection pooling
engine = create_engine(
    TIMESCALE_URL,
    poolclass=QueuePool,
    pool_size=5,
    max_overflow=10,
    pool_pre_ping=True,
    pool_recycle=3600
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_timescale_db():
    """Initialize TimescaleDB tables and hypertables"""
    with engine.connect() as conn:
        # Enable TimescaleDB extension
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS timescaledb CASCADE;"))
        conn.commit()
        
        # Create klines table
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS klines (
                time TIMESTAMPTZ NOT NULL,
                symbol VARCHAR(20) NOT NULL,
                timeframe VARCHAR(10) NOT NULL,
                open DOUBLE PRECISION NOT NULL,
                high DOUBLE PRECISION NOT NULL,
                low DOUBLE PRECISION NOT NULL,
                close DOUBLE PRECISION NOT NULL,
                volume DOUBLE PRECISION NOT NULL,
                quote_volume DOUBLE PRECISION,
                trades INTEGER,
                PRIMARY KEY (time, symbol, timeframe)
            );
        """))
        conn.commit()
        
        # Convert to hypertable
        try:
            conn.execute(text("""
                SELECT create_hypertable('klines', 'time', 
                    chunk_time_interval => INTERVAL '1 day',
                    if_not_exists => TRUE
                );
            """))
            conn.commit()
        except Exception as e:
            if "already a hypertable" not in str(e):
                logger.warning(f"Hypertable creation warning: {e}")
        
        # Create indexes
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_klines_symbol_time 
            ON klines (symbol, time DESC);
        """))
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_klines_timeframe 
            ON klines (timeframe, time DESC);
        """))
        conn.commit()
        
        logger.info("TimescaleDB initialized successfully")


@contextmanager
def get_ts_db():
    """Get TimescaleDB session context manager"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def save_klines(symbol: str, timeframe: str, klines: List[List]) -> int:
    """Save K-line data to TimescaleDB"""
    if not klines:
        return 0
    
    with get_ts_db() as db:
        values = []
        for k in klines:
            timestamp = datetime.fromtimestamp(k[0] / 1000)
            values.append({
                'time': timestamp,
                'symbol': symbol,
                'timeframe': timeframe,
                'open': float(k[1]),
                'high': float(k[2]),
                'low': float(k[3]),
                'close': float(k[4]),
                'volume': float(k[5]),
                'quote_volume': float(k[6]) if len(k) > 6 else None,
                'trades': int(k[7]) if len(k) > 7 else None
            })
        
        insert_sql = text("""
            INSERT INTO klines (time, symbol, timeframe, open, high, low, close, volume, quote_volume, trades)
            VALUES (:time, :symbol, :timeframe, :open, :high, :low, :close, :volume, :quote_volume, :trades)
            ON CONFLICT (time, symbol, timeframe) 
            DO UPDATE SET 
                open = EXCLUDED.open,
                high = EXCLUDED.high,
                low = EXCLUDED.low,
                close = EXCLUDED.close,
                volume = EXCLUDED.volume,
                quote_volume = EXCLUDED.quote_volume,
                trades = EXCLUDED.trades
        """)
        
        for v in values:
            db.execute(insert_sql, v)
        
        db.commit()
        return len(values)


def get_klines(
    symbol: str, 
    timeframe: str, 
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
    limit: int = 1000
) -> List[Dict]:
    """Get K-line data from TimescaleDB"""
    with get_ts_db() as db:
        query = """
            SELECT time, symbol, timeframe, open, high, low, close, volume, quote_volume, trades
            FROM klines
            WHERE symbol = :symbol AND timeframe = :timeframe
        """
        params = {'symbol': symbol, 'timeframe': timeframe}
        
        if start_time:
            query += " AND time >= :start_time"
            params['start_time'] = start_time
        
        if end_time:
            query += " AND time <= :end_time"
            params['end_time'] = end_time
        
        query += " ORDER BY time DESC LIMIT :limit"
        params['limit'] = limit
        
        result = db.execute(text(query), params)
        rows = result.fetchall()
        
        return [
            {
                'time': row[0],
                'symbol': row[1],
                'timeframe': row[2],
                'open': row[3],
                'high': row[4],
                'low': row[5],
                'close': row[6],
                'volume': row[7],
                'quote_volume': row[8],
                'trades': row[9]
            }
            for row in rows
        ]


def get_latest_kline_time(symbol: str, timeframe: str) -> Optional[datetime]:
    """Get the timestamp of the latest K-line for a symbol"""
    with get_ts_db() as db:
        result = db.execute(text("""
            SELECT MAX(time) FROM klines
            WHERE symbol = :symbol AND timeframe = :timeframe
        """), {'symbol': symbol, 'timeframe': timeframe})
        row = result.fetchone()
        return row[0] if row and row[0] else None


def get_kline_stats() -> Dict[str, Any]:
    """Get statistics about stored K-line data"""
    with get_ts_db() as db:
        result = db.execute(text("""
            SELECT 
                COUNT(DISTINCT symbol) as symbols,
                COUNT(*) as total_rows,
                MIN(time) as earliest,
                MAX(time) as latest
            FROM klines
        """))
        row = result.fetchone()
        
        if row:
            return {
                'symbols': row[0],
                'total_rows': row[1],
                'earliest': row[2],
                'latest': row[3]
            }
        return {}


def cleanup_old_klines(days_to_keep: int = 15) -> int:
    """Clean up old K-line data"""
    with get_ts_db() as db:
        cutoff = datetime.utcnow() - timedelta(days=days_to_keep)
        result = db.execute(text("""
            DELETE FROM klines WHERE time < :cutoff
        """), {'cutoff': cutoff})
        db.commit()
        return result.rowcount


# Timeframe aggregation mappings
TIMEFRAME_MINUTES = {
    '5m': 5,
    '15m': 15,
    '1h': 60,
    '4h': 240,
    '1d': 1440
}


def get_aggregated_klines(
    symbol: str,
    timeframe: str,
    limit: int = 500
) -> List[Dict]:
    """
    Get aggregated K-line data from 5m base data

    Args:
        symbol: Trading pair symbol
        timeframe: Target timeframe (15m, 1h, 4h, 1d)
        limit: Number of candles to return

    Returns:
        List of aggregated OHLCV data
    """
    if timeframe == '5m':
        # No aggregation needed for 5m
        return get_klines(symbol, '5m', limit=limit)

    minutes = TIMEFRAME_MINUTES.get(timeframe, 5)
    interval = f'{minutes} minutes'

    with get_ts_db() as db:
        # Use TimescaleDB time_bucket for aggregation
        query = text(f"""
            SELECT
                time_bucket('{interval}', time) AS bucket_time,
                :symbol AS symbol,
                :timeframe AS timeframe,
                (array_agg(open ORDER BY time ASC))[1] AS open,
                MAX(high) AS high,
                MIN(low) AS low,
                (array_agg(close ORDER BY time DESC))[1] AS close,
                SUM(volume) AS volume,
                SUM(quote_volume) AS quote_volume,
                SUM(trades) AS trades
            FROM klines
            WHERE symbol = :symbol AND timeframe = '5m'
            GROUP BY bucket_time
            ORDER BY bucket_time DESC
            LIMIT :limit
        """)

        result = db.execute(query, {
            'symbol': symbol,
            'timeframe': timeframe,
            'limit': limit
        })
        rows = result.fetchall()

        return [
            {
                'time': row[0],
                'symbol': row[1],
                'timeframe': row[2],
                'open': float(row[3]) if row[3] else 0,
                'high': float(row[4]) if row[4] else 0,
                'low': float(row[5]) if row[5] else 0,
                'close': float(row[6]) if row[6] else 0,
                'volume': float(row[7]) if row[7] else 0,
                'quote_volume': float(row[8]) if row[8] else 0,
                'trades': int(row[9]) if row[9] else 0
            }
            for row in rows
        ]


def has_sufficient_data(symbol: str, min_candles: int = 100) -> bool:
    """Check if we have enough 5m data for a symbol"""
    with get_ts_db() as db:
        result = db.execute(text("""
            SELECT COUNT(*) FROM klines
            WHERE symbol = :symbol AND timeframe = '5m'
        """), {'symbol': symbol})
        row = result.fetchone()
        return row[0] >= min_candles if row else False


def get_symbols_with_data() -> List[str]:
    """Get list of symbols that have 5m data in the database"""
    with get_ts_db() as db:
        result = db.execute(text("""
            SELECT DISTINCT symbol FROM klines
            WHERE timeframe = '5m'
            ORDER BY symbol
        """))
        return [row[0] for row in result.fetchall()]

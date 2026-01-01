"""
K-line Collector Service
只采集 5 分钟 K 线数据，其他周期通过数据库聚合生成
"""

import time
import logging
from typing import List, Optional
from datetime import datetime, timedelta

from backend.services.binance_service import BinanceService
from backend.database.timescale_db import save_klines, get_latest_kline_time, get_symbols_with_data

logger = logging.getLogger(__name__)

# Collection settings
BATCH_SIZE = 50  # Number of symbols to process per batch
BATCH_DELAY = 2  # Seconds to wait between batches
API_DELAY = 0.2  # Seconds to wait between API calls
MAX_CANDLES_PER_REQUEST = 500  # Binance limit


class KlineCollector:
    """Collector for 5m K-line data"""

    def __init__(self):
        self.binance = BinanceService()
        self._last_collection_time = 0
        self._collection_interval = 300  # 5 minutes

    def collect_symbol_klines(
        self,
        symbol: str,
        since: Optional[datetime] = None,
        limit: int = MAX_CANDLES_PER_REQUEST
    ) -> int:
        """
        Collect 5m K-lines for a single symbol

        Args:
            symbol: Trading pair symbol
            since: Start time (optional, defaults to last stored time)
            limit: Max candles to fetch

        Returns:
            Number of K-lines saved
        """
        try:
            # Get last stored time for incremental update
            if since is None:
                last_time = get_latest_kline_time(symbol, '5m')
                if last_time:
                    # Start from last stored time
                    since = last_time
                else:
                    # First collection: get last 24 hours
                    since = datetime.utcnow() - timedelta(hours=24)

            # Convert to milliseconds for Binance API
            since_ms = int(since.timestamp() * 1000)

            time.sleep(API_DELAY)  # Rate limiting

            # Fetch from Binance
            ohlcv = self.binance.public_exchange.fetch_ohlcv(
                symbol, '5m', since_ms, limit
            )

            if not ohlcv:
                return 0

            # Save to TimescaleDB
            saved = save_klines(symbol, '5m', ohlcv)
            return saved

        except Exception as e:
            logger.error(f"Error collecting klines for {symbol}: {e}")
            return 0

    def collect_all_symbols(
        self,
        symbols: Optional[List[str]] = None,
        initial_load: bool = False
    ) -> dict:
        """
        Collect 5m K-lines for multiple symbols

        Args:
            symbols: List of symbols (optional, defaults to all altcoins)
            initial_load: If True, load more historical data

        Returns:
            Collection statistics
        """
        if symbols is None:
            symbols = self.binance.get_altcoins()
            # Also include BTC and ETH
            symbols = ['BTC/USDT', 'ETH/USDT'] + symbols

        total_symbols = len(symbols)
        total_saved = 0
        errors = 0

        logger.info(f"Starting K-line collection for {total_symbols} symbols...")

        # Process in batches
        for i in range(0, total_symbols, BATCH_SIZE):
            batch = symbols[i:i + BATCH_SIZE]
            batch_saved = 0

            for symbol in batch:
                try:
                    if initial_load:
                        # Load 7 days of historical data for initial load
                        since = datetime.utcnow() - timedelta(days=7)
                        saved = self.collect_symbol_klines(symbol, since=since)
                    else:
                        # Incremental update
                        saved = self.collect_symbol_klines(symbol)

                    batch_saved += saved
                    total_saved += saved

                except Exception as e:
                    logger.error(f"Error processing {symbol}: {e}")
                    errors += 1

            logger.info(
                f"Batch {i // BATCH_SIZE + 1}/{(total_symbols + BATCH_SIZE - 1) // BATCH_SIZE}: "
                f"Saved {batch_saved} K-lines"
            )

            # Delay between batches
            if i + BATCH_SIZE < total_symbols:
                time.sleep(BATCH_DELAY)

        self._last_collection_time = time.time()

        result = {
            'symbols': total_symbols,
            'saved': total_saved,
            'errors': errors,
            'timestamp': datetime.utcnow().isoformat()
        }

        logger.info(f"K-line collection completed: {result}")
        return result

    def collect_top_symbols(self, top_n: int = 100) -> dict:
        """
        Collect K-lines for top N symbols by volume
        This is a lighter collection for frequent updates
        """
        try:
            # Get all tickers to sort by volume
            tickers = self.binance.fetch_24h_tickers()

            # Filter USDT pairs and sort by volume
            usdt_tickers = [
                (symbol, data)
                for symbol, data in tickers.items()
                if symbol.endswith('/USDT')
                and not any(x in symbol for x in ['UP/', 'DOWN/', 'BEAR/', 'BULL/'])
            ]

            # Sort by quote volume and take top N
            usdt_tickers.sort(
                key=lambda x: x[1].get('quoteVolume', 0) or 0,
                reverse=True
            )
            top_symbols = [t[0] for t in usdt_tickers[:top_n]]

            # Always include BTC and ETH
            if 'BTC/USDT' not in top_symbols:
                top_symbols.insert(0, 'BTC/USDT')
            if 'ETH/USDT' not in top_symbols:
                top_symbols.insert(1, 'ETH/USDT')

            return self.collect_all_symbols(top_symbols)

        except Exception as e:
            logger.error(f"Error in collect_top_symbols: {e}")
            return {'error': str(e)}

    def should_collect(self) -> bool:
        """Check if enough time has passed since last collection"""
        return (time.time() - self._last_collection_time) >= self._collection_interval


# Global collector instance
_collector = None


def get_kline_collector() -> KlineCollector:
    """Get or create the global K-line collector instance"""
    global _collector
    if _collector is None:
        _collector = KlineCollector()
    return _collector

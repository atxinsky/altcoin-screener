"""
K-line Collector Service
后台持续采集 5 分钟 K 线数据，遵守 Binance API 限制
"""

import time
import logging
import threading
from typing import List, Optional, Set
from datetime import datetime, timedelta

from backend.services.binance_service import BinanceService
from backend.database.timescale_db import save_klines, get_latest_kline_time

logger = logging.getLogger(__name__)

# Binance API 限制配置
# Weight limit: 1200/min, 每个 klines 请求约 1-2 weight
API_DELAY_BETWEEN_SYMBOLS = 0.5  # 每个币之间延迟 0.5 秒
API_DELAY_BETWEEN_BATCHES = 5    # 每批次之间延迟 5 秒
BATCH_SIZE = 20                   # 每批次处理 20 个币
MAX_CANDLES_PER_REQUEST = 500     # 每次请求最多 500 根 K 线
COLLECTION_CYCLE_DELAY = 60       # 完成一轮后等待 60 秒再开始下一轮


class KlineCollector:
    """后台持续采集 5m K 线数据"""

    def __init__(self):
        self.binance = BinanceService()
        self._is_running = False
        self._thread = None
        self._collected_symbols: Set[str] = set()
        self._last_full_cycle = 0
        self._stats = {
            'total_saved': 0,
            'errors': 0,
            'last_update': None,
            'symbols_collected': 0
        }

    def collect_symbol_klines(
        self,
        symbol: str,
        since: Optional[datetime] = None,
        limit: int = MAX_CANDLES_PER_REQUEST
    ) -> int:
        """采集单个币的 5m K 线"""
        try:
            # 获取增量更新的起始时间
            if since is None:
                last_time = get_latest_kline_time(symbol, '5m')
                if last_time:
                    since = last_time
                else:
                    # 首次采集：获取最近 24 小时
                    since = datetime.utcnow() - timedelta(hours=24)

            since_ms = int(since.timestamp() * 1000)

            # 调用 API
            ohlcv = self.binance.public_exchange.fetch_ohlcv(
                symbol, '5m', since_ms, limit
            )

            if not ohlcv:
                return 0

            # 保存到 TimescaleDB
            saved = save_klines(symbol, '5m', ohlcv)
            self._stats['total_saved'] += saved
            return saved

        except Exception as e:
            if '418' in str(e) or 'banned' in str(e).lower():
                logger.warning(f"API rate limited, will retry later: {e}")
                time.sleep(60)  # 被封禁时等待 1 分钟
            else:
                logger.error(f"Error collecting klines for {symbol}: {e}")
            self._stats['errors'] += 1
            return 0

    def _collection_loop(self):
        """后台采集循环"""
        logger.info("K-line collector background loop started")

        while self._is_running:
            try:
                # 获取所有交易对
                symbols = self.binance.get_all_spot_symbols()
                if not symbols:
                    logger.warning("No symbols fetched, waiting...")
                    time.sleep(30)
                    continue

                # 确保 BTC 和 ETH 优先
                priority_symbols = ['BTC/USDT', 'ETH/USDT']
                other_symbols = [s for s in symbols if s not in priority_symbols]
                all_symbols = priority_symbols + other_symbols

                logger.info(f"Starting collection cycle for {len(all_symbols)} symbols")
                cycle_saved = 0
                cycle_start = time.time()

                # 分批处理
                for i in range(0, len(all_symbols), BATCH_SIZE):
                    if not self._is_running:
                        break

                    batch = all_symbols[i:i + BATCH_SIZE]
                    batch_saved = 0

                    for symbol in batch:
                        if not self._is_running:
                            break

                        saved = self.collect_symbol_klines(symbol)
                        batch_saved += saved
                        self._collected_symbols.add(symbol)

                        # 币之间延迟
                        time.sleep(API_DELAY_BETWEEN_SYMBOLS)

                    cycle_saved += batch_saved
                    batch_num = i // BATCH_SIZE + 1
                    total_batches = (len(all_symbols) + BATCH_SIZE - 1) // BATCH_SIZE

                    logger.info(
                        f"Batch {batch_num}/{total_batches}: "
                        f"saved {batch_saved} candles"
                    )

                    # 批次之间延迟
                    if i + BATCH_SIZE < len(all_symbols):
                        time.sleep(API_DELAY_BETWEEN_BATCHES)

                # 更新统计
                cycle_time = time.time() - cycle_start
                self._stats['symbols_collected'] = len(self._collected_symbols)
                self._stats['last_update'] = datetime.utcnow().isoformat()
                self._last_full_cycle = time.time()

                logger.info(
                    f"Collection cycle completed: {cycle_saved} candles "
                    f"from {len(all_symbols)} symbols in {cycle_time:.1f}s"
                )

                # 等待下一个周期
                time.sleep(COLLECTION_CYCLE_DELAY)

            except Exception as e:
                logger.error(f"Error in collection loop: {e}")
                time.sleep(30)

        logger.info("K-line collector background loop stopped")

    def start(self):
        """启动后台采集"""
        if self._is_running:
            return

        self._is_running = True
        self._thread = threading.Thread(target=self._collection_loop, daemon=True)
        self._thread.start()
        logger.info("K-line collector started")

    def stop(self):
        """停止后台采集"""
        self._is_running = False
        if self._thread:
            self._thread.join(timeout=5)
        logger.info("K-line collector stopped")

    def get_stats(self) -> dict:
        """获取采集统计"""
        return {
            **self._stats,
            'is_running': self._is_running,
            'collected_symbols': len(self._collected_symbols)
        }

    def force_refresh_symbol(self, symbol: str) -> int:
        """强制刷新单个币的 K 线（手动刷新用）"""
        # 获取最近 2 小时的数据
        since = datetime.utcnow() - timedelta(hours=2)
        return self.collect_symbol_klines(symbol, since=since)

    def force_refresh_symbols(self, symbols: List[str]) -> dict:
        """强制刷新多个币的 K 线（手动刷新用）"""
        total_saved = 0
        errors = 0

        for symbol in symbols:
            try:
                saved = self.force_refresh_symbol(symbol)
                total_saved += saved
                time.sleep(0.2)  # 小延迟
            except Exception as e:
                logger.error(f"Error refreshing {symbol}: {e}")
                errors += 1

        return {
            'symbols': len(symbols),
            'saved': total_saved,
            'errors': errors
        }


# 全局采集器实例
_collector = None
_lock = threading.Lock()


def get_kline_collector() -> KlineCollector:
    """获取全局 K 线采集器实例"""
    global _collector
    with _lock:
        if _collector is None:
            _collector = KlineCollector()
        return _collector


def start_background_collector():
    """启动后台采集器（在应用启动时调用）"""
    collector = get_kline_collector()
    collector.start()
    return collector


def stop_background_collector():
    """停止后台采集器"""
    global _collector
    if _collector:
        _collector.stop()

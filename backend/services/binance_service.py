import ccxt
import pandas as pd
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import asyncio
from backend.config import settings


class BinanceService:
    """Service for interacting with Binance API"""

    def __init__(self):
        # 带API密钥的客户端 - 用于交易、余额查询等需要认证的操作
        self.exchange = ccxt.binance({
            'apiKey': settings.BINANCE_API_KEY,
            'secret': settings.BINANCE_API_SECRET,
            'enableRateLimit': True,
            'options': {
                'defaultType': 'spot',
            }
        })

        # 不带API密钥的公开客户端 - 用于获取K线、市场数据等公开信息
        # 避免因API密钥IP白名单限制导致公开数据请求失败
        self.public_exchange = ccxt.binance({
            'enableRateLimit': True,
            'options': {
                'defaultType': 'spot',
            }
        })

    def get_all_spot_symbols(self) -> List[str]:
        """Get all ACTIVE spot trading symbols from Binance"""
        try:
            markets = self.public_exchange.load_markets()
            # Filter for USDT spot pairs that are ACTIVE, exclude leveraged tokens
            symbols = [
                symbol for symbol, market in markets.items()
                if market['quote'] == 'USDT'
                and market['spot']
                and market.get('active', False)  # 只返回活跃的交易对
                and not any(x in symbol for x in ['UP/', 'DOWN/', 'BEAR/', 'BULL/'])
            ]
            print(f"获取到 {len(symbols)} 个活跃的USDT现货交易对")
            return symbols
        except Exception as e:
            print(f"Error fetching symbols: {e}")
            return []

    def get_altcoins(self) -> List[str]:
        """Get altcoin symbols (excluding BTC and ETH)"""
        all_symbols = self.get_all_spot_symbols()
        # Exclude BTC, ETH and stablecoins (base currency only)
        stablecoins = ['USDT/USDT', 'USDC/USDT', 'BUSD/USDT', 'DAI/USDT', 'TUSD/USDT', 'USDP/USDT', 'FDUSD/USDT']
        altcoins = [
            s for s in all_symbols
            if s not in ['BTC/USDT', 'ETH/USDT'] + stablecoins
        ]
        return altcoins

    def fetch_ohlcv(
        self,
        symbol: str,
        timeframe: str = '5m',
        limit: int = 500,
        since: Optional[int] = None
    ) -> pd.DataFrame:
        """
        Fetch OHLCV (candlestick) data

        Args:
            symbol: Trading pair symbol (e.g., 'BTC/USDT')
            timeframe: Timeframe (1m, 5m, 15m, 1h, 4h, 1d)
            limit: Number of candles to fetch
            since: Timestamp in milliseconds

        Returns:
            DataFrame with OHLCV data
        """
        try:
            # 使用公开客户端获取K线数据（不需要API密钥）
            ohlcv = self.public_exchange.fetch_ohlcv(symbol, timeframe, since, limit)
            df = pd.DataFrame(
                ohlcv,
                columns=['timestamp', 'open', 'high', 'low', 'close', 'volume']
            )
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            # Calculate quote volume (volume in quote currency, e.g., USDT)
            # Use average price (OHLC/4) * volume as approximation
            df['quote_volume'] = ((df['open'] + df['high'] + df['low'] + df['close']) / 4) * df['volume']
            df['symbol'] = symbol
            df['timeframe'] = timeframe
            return df
        except Exception as e:
            print(f"Error fetching OHLCV for {symbol}: {e}")
            return pd.DataFrame()

    def fetch_ticker(self, symbol: str) -> Dict:
        """Fetch current ticker data"""
        try:
            # 使用公开客户端获取ticker数据
            ticker = self.public_exchange.fetch_ticker(symbol)
            return ticker
        except Exception as e:
            print(f"Error fetching ticker for {symbol}: {e}")
            return {}

    def fetch_24h_tickers(self) -> Dict[str, Dict]:
        """Fetch 24h ticker data for all symbols"""
        try:
            # 使用公开客户端获取所有ticker数据
            tickers = self.public_exchange.fetch_tickers()
            return tickers
        except Exception as e:
            print(f"Error fetching 24h tickers: {e}")
            return {}

    def get_historical_data(
        self,
        symbol: str,
        timeframe: str,
        days: int = 30
    ) -> pd.DataFrame:
        """
        Fetch historical data for a specified number of days

        Args:
            symbol: Trading pair symbol
            timeframe: Timeframe
            days: Number of days of historical data

        Returns:
            DataFrame with historical OHLCV data
        """
        all_data = []
        # 使用公开客户端获取历史数据
        since = self.public_exchange.parse8601(
            (datetime.utcnow() - timedelta(days=days)).isoformat()
        )

        while True:
            try:
                ohlcv = self.public_exchange.fetch_ohlcv(symbol, timeframe, since, 1000)
                if not ohlcv:
                    break

                all_data.extend(ohlcv)

                # Update since to the last timestamp
                since = ohlcv[-1][0] + 1

                # Check if we've reached the current time
                if datetime.fromtimestamp(since / 1000) >= datetime.utcnow():
                    break

            except Exception as e:
                print(f"Error fetching historical data for {symbol}: {e}")
                break

        if all_data:
            df = pd.DataFrame(
                all_data,
                columns=['timestamp', 'open', 'high', 'low', 'close', 'volume']
            )
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            df['symbol'] = symbol
            df['timeframe'] = timeframe
            df = df.drop_duplicates(subset=['timestamp']).reset_index(drop=True)
            return df
        else:
            return pd.DataFrame()

    def calculate_price_ratios(
        self,
        altcoin_price: float,
        btc_price: float,
        eth_price: float
    ) -> Dict[str, float]:
        """Calculate price ratios against BTC and ETH"""
        return {
            'btc_ratio': altcoin_price / btc_price if btc_price > 0 else 0,
            'eth_ratio': altcoin_price / eth_price if eth_price > 0 else 0
        }

    def get_market_overview(self) -> Dict:
        """Get BTC and ETH prices for market context"""
        try:
            btc_ticker = self.fetch_ticker('BTC/USDT')
            eth_ticker = self.fetch_ticker('ETH/USDT')

            return {
                'btc_price': btc_ticker.get('last', 0),
                'eth_price': eth_ticker.get('last', 0),
                'btc_change_24h': btc_ticker.get('percentage', 0),
                'eth_change_24h': eth_ticker.get('percentage', 0),
            }
        except Exception as e:
            print(f"Error getting market overview: {e}")
            return {
                'btc_price': 0,
                'eth_price': 0,
                'btc_change_24h': 0,
                'eth_change_24h': 0,
            }

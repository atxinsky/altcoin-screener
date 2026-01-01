import ccxt
import pandas as pd
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import asyncio
import time
from backend.config import settings

# Try to import TimescaleDB functions (optional)
try:
    from backend.database.timescale_db import get_aggregated_klines, has_sufficient_data
    TIMESCALE_AVAILABLE = True
except ImportError:
    TIMESCALE_AVAILABLE = False


# Global cache for market data to prevent rate limiting
_market_cache = {
    'btc_ticker': None,
    'eth_ticker': None,
    'last_update': 0,
    'symbols': None,
    'symbols_update': 0,
    'tickers': None,
    'tickers_update': 0,
}
_CACHE_TTL = 30  # Cache TTL in seconds for prices
_SYMBOLS_CACHE_TTL = 300  # Cache symbols for 5 minutes
_TICKERS_CACHE_TTL = 60  # Cache tickers for 1 minute
_API_DELAY = 0.1  # Delay between API calls in seconds


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

    def _get_prices_from_coingecko(self) -> Dict:
        """Fallback: Get BTC/ETH prices from CoinGecko API"""
        try:
            import requests
            response = requests.get(
                'https://api.coingecko.com/api/v3/simple/price',
                params={
                    'ids': 'bitcoin,ethereum',
                    'vs_currencies': 'usd',
                    'include_24hr_change': 'true'
                },
                timeout=10
            )
            if response.status_code == 200:
                data = response.json()
                return {
                    'btc': {
                        'last': data.get('bitcoin', {}).get('usd', 0),
                        'percentage': data.get('bitcoin', {}).get('usd_24h_change', 0)
                    },
                    'eth': {
                        'last': data.get('ethereum', {}).get('usd', 0),
                        'percentage': data.get('ethereum', {}).get('usd_24h_change', 0)
                    }
                }
        except Exception as e:
            print(f'CoinGecko fallback failed: {e}')
        return None

    def get_all_spot_symbols(self) -> List[str]:
        """Get all ACTIVE spot trading symbols from Binance (with caching)"""
        global _market_cache
        
        current_time = time.time()
        
        # Return cached symbols if valid
        if _market_cache['symbols'] and (current_time - _market_cache['symbols_update']) < _SYMBOLS_CACHE_TTL:
            return _market_cache['symbols']
        
        try:
            time.sleep(_API_DELAY)  # Rate limiting delay
            markets = self.public_exchange.load_markets()
            # Filter for USDT spot pairs that are ACTIVE, exclude leveraged tokens
            symbols = [
                symbol for symbol, market in markets.items()
                if market['quote'] == 'USDT'
                and market['spot']
                and market.get('active', False)  # 只返回活跃的交易对
                and not any(x in symbol for x in ['UP/', 'DOWN/', 'BEAR/', 'BULL/'])
            ]
            # Update cache
            _market_cache['symbols'] = symbols
            _market_cache['symbols_update'] = current_time
            print(f"获取到 {len(symbols)} 个活跃的USDT现货交易对 (已缓存)")
            return symbols
        except Exception as e:
            print(f"Error fetching symbols: {e}")
            # Return cached data if available, even if expired
            if _market_cache['symbols']:
                print(f"Using cached symbols ({len(_market_cache['symbols'])} symbols)")
                return _market_cache['symbols']
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
            time.sleep(_API_DELAY)  # Rate limiting delay
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

    def fetch_ohlcv_smart(
        self,
        symbol: str,
        timeframe: str = '5m',
        limit: int = 500
    ) -> pd.DataFrame:
        """
        Smart OHLCV fetch: tries database first, then API
        For 15m/1h/4h/1d, uses aggregated 5m data from database
        """
        # Try database first for aggregated data
        if TIMESCALE_AVAILABLE and timeframe != '5m':
            try:
                if has_sufficient_data(symbol, min_candles=50):
                    klines = get_aggregated_klines(symbol, timeframe, limit)
                    if klines:
                        df = pd.DataFrame(klines)
                        df['timestamp'] = pd.to_datetime(df['time'])
                        df = df.rename(columns={'time': 'timestamp'})
                        df['symbol'] = symbol
                        df['timeframe'] = timeframe
                        return df[['timestamp', 'open', 'high', 'low', 'close', 'volume', 'quote_volume', 'symbol', 'timeframe']]
            except Exception as e:
                print(f"Database fetch failed for {symbol}, falling back to API: {e}")
        
        # Fallback to API
        return self.fetch_ohlcv(symbol, timeframe, limit)

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
        """Fetch 24h ticker data for all symbols (with caching)"""
        global _market_cache
        
        current_time = time.time()
        
        # Return cached tickers if valid
        if _market_cache['tickers'] and (current_time - _market_cache['tickers_update']) < _TICKERS_CACHE_TTL:
            return _market_cache['tickers']
        
        try:
            time.sleep(_API_DELAY)  # Rate limiting delay
            # 使用公开客户端获取所有ticker数据
            tickers = self.public_exchange.fetch_tickers()
            # Update cache
            _market_cache['tickers'] = tickers
            _market_cache['tickers_update'] = current_time
            return tickers
        except Exception as e:
            print(f"Error fetching 24h tickers: {e}")
            # Return cached data if available
            if _market_cache['tickers']:
                print("Using cached tickers")
                return _market_cache['tickers']
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
        """Get BTC and ETH prices for market context with caching and fallback"""
        global _market_cache
        
        current_time = time.time()
        cache_valid = (current_time - _market_cache['last_update']) < _CACHE_TTL
        
        # Try to get fresh data from Binance
        btc_ticker = None
        eth_ticker = None
        
        if not cache_valid:
            try:
                btc_ticker = self.fetch_ticker('BTC/USDT')
                eth_ticker = self.fetch_ticker('ETH/USDT')
                
                # Update cache if we got valid data
                if btc_ticker and btc_ticker.get('last', 0) > 0:
                    _market_cache['btc_ticker'] = btc_ticker
                if eth_ticker and eth_ticker.get('last', 0) > 0:
                    _market_cache['eth_ticker'] = eth_ticker
                if (btc_ticker and btc_ticker.get('last', 0) > 0) or (eth_ticker and eth_ticker.get('last', 0) > 0):
                    _market_cache['last_update'] = current_time
            except Exception as e:
                print(f"Error fetching tickers from Binance: {e}")
        
        # Use cached data if available
        btc_ticker = _market_cache.get('btc_ticker') or {}
        eth_ticker = _market_cache.get('eth_ticker') or {}
        
        # Fallback to CoinGecko if no valid data
        if btc_ticker.get('last', 0) == 0 or eth_ticker.get('last', 0) == 0:
            print("Using CoinGecko fallback for BTC/ETH prices...")
            coingecko_data = self._get_prices_from_coingecko()
            if coingecko_data:
                if btc_ticker.get('last', 0) == 0:
                    btc_ticker = coingecko_data['btc']
                    _market_cache['btc_ticker'] = btc_ticker
                if eth_ticker.get('last', 0) == 0:
                    eth_ticker = coingecko_data['eth']
                    _market_cache['eth_ticker'] = eth_ticker
                _market_cache['last_update'] = current_time
        
        # Get Fear & Greed Index from CMC (with alternative.me fallback)
        fear_greed = self._get_fear_greed_index()

        # Get Altcoin Season Index from blockchaincenter.net
        altcoin_season = self._get_altcoin_season_index()

        return {
            'btc_price': btc_ticker.get('last', 0),
            'eth_price': eth_ticker.get('last', 0),
            'btc_change_24h': btc_ticker.get('percentage', 0),
            'eth_change_24h': eth_ticker.get('percentage', 0),
            'fear_greed_index': fear_greed.get('value', 0),
            'fear_greed_label': fear_greed.get('label', 'N/A'),
            'altcoin_season_index': altcoin_season.get('value', 0),
            'altcoin_season_label': altcoin_season.get('label', 'N/A'),
        }

    def _get_fear_greed_index(self) -> Dict:
        """Get CMC Crypto Fear & Greed Index by scraping CoinMarketCap page"""
        try:
            import requests
            import re

            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            }

            response = requests.get(
                'https://coinmarketcap.com/charts/fear-and-greed-index/',
                headers=headers,
                timeout=10
            )

            if response.status_code == 200:
                html = response.text

                # Look for the fear and greed value in the page
                # CMC embeds the data in __NEXT_DATA__ JSON
                import json
                next_data_match = re.search(r'<script id="__NEXT_DATA__" type="application/json">(.+?)</script>', html)

                if next_data_match:
                    try:
                        next_data = json.loads(next_data_match.group(1))
                        # Navigate to fear and greed data
                        page_props = next_data.get('props', {}).get('pageProps', {})
                        fng_data = page_props.get('fearGreedIndex', {})

                        if fng_data:
                            value = int(fng_data.get('score', 0))
                            # Determine label based on value
                            if value >= 75:
                                label = 'Extreme Greed'
                            elif value >= 55:
                                label = 'Greed'
                            elif value >= 45:
                                label = 'Neutral'
                            elif value >= 25:
                                label = 'Fear'
                            else:
                                label = 'Extreme Fear'

                            return {'value': value, 'label': label}
                    except json.JSONDecodeError:
                        pass

                # Fallback: try regex patterns
                value_match = re.search(r'"score"\s*:\s*(\d+)', html)
                if value_match:
                    value = int(value_match.group(1))
                    if value >= 75:
                        label = 'Extreme Greed'
                    elif value >= 55:
                        label = 'Greed'
                    elif value >= 45:
                        label = 'Neutral'
                    elif value >= 25:
                        label = 'Fear'
                    else:
                        label = 'Extreme Fear'
                    return {'value': value, 'label': label}

        except Exception as e:
            print(f"Error getting CMC Fear & Greed index: {e}")

        # Fallback to alternative.me if CMC fails
        try:
            import requests
            response = requests.get('https://api.alternative.me/fng/?limit=1', timeout=5)
            if response.status_code == 200:
                data = response.json()
                if data.get('data') and len(data['data']) > 0:
                    fng = data['data'][0]
                    return {
                        'value': int(fng.get('value', 0)),
                        'label': fng.get('value_classification', 'N/A')
                    }
        except Exception as e:
            print(f"Error getting alternative.me Fear & Greed index: {e}")

        return {'value': 0, 'label': 'N/A'}

    def _get_altcoin_season_index(self) -> Dict:
        """Get CMC Altcoin Season Index by scraping CoinMarketCap page"""
        try:
            import requests
            import re

            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            }

            response = requests.get(
                'https://coinmarketcap.com/charts/altcoin-season-index/',
                headers=headers,
                timeout=10
            )

            if response.status_code == 200:
                html = response.text

                # Look for altcoinIndex in page data
                value_match = re.search(r'altcoinIndex["\']?\s*:\s*(\d+)', html)

                if value_match:
                    value = int(value_match.group(1))

                    # Determine label based on CMC methodology
                    # >= 75: Altcoin Season, <= 25: Bitcoin Season
                    if value >= 75:
                        label = 'Altcoin Season'
                    elif value >= 50:
                        label = 'Altcoin Month'
                    elif value >= 25:
                        label = 'Bitcoin Month'
                    else:
                        label = 'Bitcoin Season'

                    return {'value': value, 'label': label}

        except Exception as e:
            print(f"Error getting CMC Altcoin Season index: {e}")

        return {'value': 0, 'label': 'N/A'}

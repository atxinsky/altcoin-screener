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
        except Exception as e:
            print(f"Error getting market overview: {e}")
            return {
                'btc_price': 0,
                'eth_price': 0,
                'btc_change_24h': 0,
                'eth_change_24h': 0,
                'fear_greed_index': 0,
                'fear_greed_label': 'N/A',
                'altcoin_season_index': 0,
                'altcoin_season_label': 'N/A',
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

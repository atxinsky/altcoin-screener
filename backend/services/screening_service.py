import pandas as pd
from typing import List, Dict, Tuple
from datetime import datetime
from sqlalchemy.orm import Session

from backend.services.binance_service import BinanceService
from backend.services.indicator_service import IndicatorService
from backend.database.models import KlineData, TechnicalIndicators, ScreeningResult
from backend.config import settings


class ScreeningService:
    """Service for screening altcoins based on various criteria"""

    def __init__(self, db: Session):
        self.db = db
        self.binance = BinanceService()
        self.indicator_service = IndicatorService()

    def screen_altcoins(
        self,
        timeframe: str = '5m',
        min_volume: float = None,
        min_price_change: float = None
    ) -> List[Dict]:
        """
        Screen altcoins based on multiple criteria

        Args:
            timeframe: Timeframe to analyze (5m, 15m, 1h, 4h)
            min_volume: Minimum 24h volume in USD
            min_price_change: Minimum price change percentage

        Returns:
            List of screening results
        """
        if min_volume is None:
            min_volume = settings.MIN_VOLUME_USD

        if min_price_change is None:
            if timeframe == '5m':
                min_price_change = settings.MIN_PRICE_CHANGE_5M
            elif timeframe == '15m':
                min_price_change = settings.MIN_PRICE_CHANGE_15M
            else:
                min_price_change = 1.0

        # Get market overview (BTC and ETH prices)
        market_overview = self.binance.get_market_overview()
        btc_price = market_overview['btc_price']
        eth_price = market_overview['eth_price']

        if btc_price == 0 or eth_price == 0:
            print("Failed to get BTC/ETH prices")
            return []

        # Get all altcoins
        all_altcoins = self.binance.get_altcoins()
        print(f"Total altcoins: {len(all_altcoins)}")

        # Pre-filter by volume to speed up screening
        print(f"Pre-filtering by volume (min: ${min_volume:,.0f})...")
        altcoins = self._prefilter_by_volume(all_altcoins, min_volume)
        print(f"After pre-filter: {len(altcoins)} altcoins")
        print(f"Screening {len(altcoins)} altcoins...")

        results = []

        for symbol in altcoins:
            try:
                result = self._screen_single_coin(
                    symbol=symbol,
                    timeframe=timeframe,
                    btc_price=btc_price,
                    eth_price=eth_price,
                    min_volume=min_volume,
                    min_price_change=min_price_change
                )

                if result:
                    results.append(result)

            except Exception as e:
                print(f"Error screening {symbol}: {e}")
                continue

        # Sort by total score
        results = sorted(results, key=lambda x: x['total_score'], reverse=True)

        # Save to database
        self._save_screening_results(results, timeframe)

        return results

    def _screen_single_coin(
        self,
        symbol: str,
        timeframe: str,
        btc_price: float,
        eth_price: float,
        min_volume: float,
        min_price_change: float
    ) -> Dict:
        """Screen a single coin"""

        # Fetch ticker for volume check
        ticker = self.binance.fetch_ticker(symbol)
        if not ticker:
            return None

        volume_24h = ticker.get('quoteVolume', 0)

        # Filter by minimum volume
        if volume_24h < min_volume:
            return None

        # Fetch OHLCV data
        df = self.binance.fetch_ohlcv(symbol, timeframe, limit=500)
        if df.empty:
            return None

        # Save K-line data to database
        self._save_kline_data(df, symbol, timeframe)

        # Calculate technical indicators
        df = self.indicator_service.calculate_all_indicators(df)

        # Get current price
        current_price = df['close'].iloc[-1]

        # Calculate price ratios
        price_btc_ratio = current_price / btc_price
        price_eth_ratio = current_price / eth_price

        # Calculate ratio changes (compare to 24h ago)
        if len(df) >= 288:  # Assuming 5m timeframe, 288 candles = 24h
            old_price = df['close'].iloc[-288]
            btc_ratio_old = old_price / btc_price
            eth_ratio_old = old_price / eth_price

            btc_ratio_change = ((price_btc_ratio - btc_ratio_old) / btc_ratio_old) * 100
            eth_ratio_change = ((price_eth_ratio - eth_ratio_old) / eth_ratio_old) * 100
        else:
            btc_ratio_change = 0
            eth_ratio_change = 0

        # Calculate price changes for different timeframes
        price_changes = self._calculate_multi_timeframe_changes(symbol)

        # Check conditions
        above_sma = self.indicator_service.check_price_above_sma(df)
        macd_golden_cross = self.indicator_service.check_macd_golden_cross(df)
        above_all_ema = self.indicator_service.check_price_above_all_ema(df)

        # Check volume surge
        volume_surge = df['volume_surge'].iloc[-1] if 'volume_surge' in df.columns else False

        # Detect price anomaly
        price_anomaly, _ = self.indicator_service.detect_price_anomaly(
            df, threshold=min_price_change
        )

        # Calculate scores
        beta_score = self._calculate_beta_score(btc_ratio_change, eth_ratio_change)
        volume_score = self._calculate_volume_score(volume_24h, volume_surge)
        technical_score = self.indicator_service.calculate_technical_score(df)

        # Calculate total score (weighted average)
        total_score = (
            beta_score * 0.3 +
            volume_score * 0.2 +
            technical_score * 0.5
        )

        # Filter: only return coins with positive beta and decent score
        if beta_score < 30 or total_score < 40:
            return None

        return {
            'symbol': symbol,
            'timestamp': datetime.utcnow(),
            'timeframe': timeframe,
            'current_price': current_price,
            'price_btc_ratio': price_btc_ratio,
            'price_eth_ratio': price_eth_ratio,
            'btc_ratio_change_pct': btc_ratio_change,
            'eth_ratio_change_pct': eth_ratio_change,
            'beta_score': beta_score,
            'volume_score': volume_score,
            'technical_score': technical_score,
            'total_score': total_score,
            'above_sma': above_sma,
            'macd_golden_cross': macd_golden_cross,
            'above_all_ema': above_all_ema,
            'volume_surge': volume_surge,
            'price_anomaly': price_anomaly,
            'price_change_5m': price_changes.get('5m', 0),
            'price_change_15m': price_changes.get('15m', 0),
            'price_change_1h': price_changes.get('1h', 0),
            'price_change_4h': price_changes.get('4h', 0),
            'volume_24h': volume_24h,
            'volume_change_pct': ticker.get('percentage', 0),
        }

    def _prefilter_by_volume(self, symbols: List[str], min_volume: float) -> List[str]:
        """
        Pre-filter symbols by 24h volume to speed up screening
        Uses batch ticker API for efficiency
        """
        try:
            # Fetch all tickers at once
            tickers = self.binance.exchange.fetch_tickers(symbols)

            # Filter by volume
            filtered = []
            for symbol in symbols:
                if symbol in tickers:
                    ticker = tickers[symbol]
                    volume_usd = ticker.get('quoteVolume', 0)
                    if volume_usd >= min_volume:
                        filtered.append(symbol)

            return filtered
        except Exception as e:
            print(f"Error in pre-filter: {e}, using all symbols")
            return symbols

    def _calculate_beta_score(
        self,
        btc_ratio_change: float,
        eth_ratio_change: float
    ) -> float:
        """
        Calculate beta score (0-100)

        Higher score = stronger performance relative to BTC/ETH
        """
        # Average of BTC and ETH ratio changes
        avg_ratio_change = (btc_ratio_change + eth_ratio_change) / 2

        # Convert to score (0-100)
        # Assuming ratio change of 5% = score of 50, 10% = 100
        score = min(100, max(0, avg_ratio_change * 10))

        return score

    def _calculate_volume_score(
        self,
        volume_24h: float,
        volume_surge: bool
    ) -> float:
        """
        Calculate volume score (0-100)

        Considers both absolute volume and volume surge
        """
        # Base score from volume
        if volume_24h >= 10000000:  # 10M+
            base_score = 100
        elif volume_24h >= 5000000:  # 5M+
            base_score = 80
        elif volume_24h >= 2000000:  # 2M+
            base_score = 60
        elif volume_24h >= 1000000:  # 1M+
            base_score = 40
        else:
            base_score = 20

        # Bonus for volume surge
        if volume_surge:
            base_score = min(100, base_score + 20)

        return base_score

    def _calculate_multi_timeframe_changes(self, symbol: str) -> Dict[str, float]:
        """Calculate price changes across multiple timeframes"""
        changes = {}

        timeframes = {
            '5m': 1,  # 1 candle back
            '15m': 1,
            '1h': 1,
            '4h': 1,
        }

        for tf, lookback in timeframes.items():
            try:
                df = self.binance.fetch_ohlcv(symbol, tf, limit=lookback + 1)
                if not df.empty and len(df) > lookback:
                    current = df['close'].iloc[-1]
                    previous = df['close'].iloc[-lookback - 1]
                    change = ((current - previous) / previous) * 100
                    changes[tf] = change
                else:
                    changes[tf] = 0
            except:
                changes[tf] = 0

        return changes

    def _save_screening_results(self, results: List[Dict], timeframe: str):
        """Save screening results to database"""
        try:
            for result in results:
                screening_result = ScreeningResult(
                    symbol=result['symbol'],
                    timestamp=result['timestamp'],
                    timeframe=timeframe,
                    price_btc_ratio=result['price_btc_ratio'],
                    price_eth_ratio=result['price_eth_ratio'],
                    btc_ratio_change_pct=result['btc_ratio_change_pct'],
                    eth_ratio_change_pct=result['eth_ratio_change_pct'],
                    beta_score=result['beta_score'],
                    volume_score=result['volume_score'],
                    technical_score=result['technical_score'],
                    total_score=result['total_score'],
                    above_sma=result['above_sma'],
                    macd_golden_cross=result['macd_golden_cross'],
                    above_all_ema=result['above_all_ema'],
                    volume_surge=result['volume_surge'],
                    price_anomaly=result['price_anomaly'],
                    price_change_5m=result['price_change_5m'],
                    price_change_15m=result['price_change_15m'],
                    price_change_1h=result['price_change_1h'],
                    price_change_4h=result['price_change_4h'],
                    volume_24h=result['volume_24h'],
                    volume_change_pct=result['volume_change_pct'],
                    current_price=result['current_price'],
                )
                self.db.add(screening_result)

            self.db.commit()
        except Exception as e:
            print(f"Error saving screening results: {e}")
            self.db.rollback()

    def _save_kline_data(self, df: pd.DataFrame, symbol: str, timeframe: str):
        """Save K-line data to database"""
        try:
            for _, row in df.iterrows():
                # Check if record already exists
                existing = self.db.query(KlineData).filter(
                    KlineData.symbol == symbol,
                    KlineData.timeframe == timeframe,
                    KlineData.timestamp == row['timestamp']
                ).first()

                if not existing:
                    kline = KlineData(
                        symbol=symbol,
                        timeframe=timeframe,
                        timestamp=row['timestamp'],
                        open=float(row['open']),
                        high=float(row['high']),
                        low=float(row['low']),
                        close=float(row['close']),
                        volume=float(row['volume'])
                    )
                    self.db.add(kline)

            self.db.commit()
        except Exception as e:
            print(f"Error saving K-line data for {symbol}: {e}")
            self.db.rollback()

    def get_top_opportunities(
        self,
        limit: int = 20,
        min_score: float = 60
    ) -> List[Dict]:
        """Get top opportunities from latest screening"""
        try:
            results = self.db.query(ScreeningResult).filter(
                ScreeningResult.total_score >= min_score
            ).order_by(
                ScreeningResult.timestamp.desc(),
                ScreeningResult.total_score.desc()
            ).limit(limit).all()

            return [self._screening_result_to_dict(r) for r in results]
        except Exception as e:
            print(f"Error getting top opportunities: {e}")
            return []

    @staticmethod
    def _screening_result_to_dict(result: ScreeningResult) -> Dict:
        """Convert ScreeningResult object to dictionary"""
        return {
            'id': result.id,
            'symbol': result.symbol,
            'timestamp': result.timestamp.isoformat(),
            'timeframe': result.timeframe,
            'current_price': result.current_price,
            'btc_ratio_change_pct': result.btc_ratio_change_pct,
            'eth_ratio_change_pct': result.eth_ratio_change_pct,
            'beta_score': result.beta_score,
            'volume_score': result.volume_score,
            'technical_score': result.technical_score,
            'total_score': result.total_score,
            'above_sma': result.above_sma,
            'macd_golden_cross': result.macd_golden_cross,
            'above_all_ema': result.above_all_ema,
            'volume_surge': result.volume_surge,
            'price_anomaly': result.price_anomaly,
            'volume_24h': result.volume_24h,
        }

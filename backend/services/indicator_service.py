import pandas as pd
import numpy as np
from typing import Dict, Tuple


class IndicatorService:
    """Service for calculating technical indicators using pure pandas/numpy"""

    @staticmethod
    def calculate_moving_averages(df: pd.DataFrame) -> pd.DataFrame:
        """Calculate various moving averages"""
        # Simple Moving Averages
        df['sma_20'] = df['close'].rolling(window=20).mean()
        df['sma_50'] = df['close'].rolling(window=50).mean()
        df['sma_200'] = df['close'].rolling(window=200).mean()

        # Exponential Moving Averages
        df['ema_7'] = df['close'].ewm(span=7, adjust=False).mean()
        df['ema_14'] = df['close'].ewm(span=14, adjust=False).mean()
        df['ema_30'] = df['close'].ewm(span=30, adjust=False).mean()
        df['ema_52'] = df['close'].ewm(span=52, adjust=False).mean()

        return df

    @staticmethod
    def calculate_macd(df: pd.DataFrame, fast=12, slow=26, signal=9) -> pd.DataFrame:
        """Calculate MACD indicator"""
        # Calculate EMAs
        ema_fast = df['close'].ewm(span=fast, adjust=False).mean()
        ema_slow = df['close'].ewm(span=slow, adjust=False).mean()

        # MACD line
        df['macd'] = ema_fast - ema_slow

        # Signal line
        df['macd_signal'] = df['macd'].ewm(span=signal, adjust=False).mean()

        # Histogram
        df['macd_histogram'] = df['macd'] - df['macd_signal']

        # Detect MACD golden cross
        df['macd_golden_cross'] = (
            (df['macd'] > df['macd_signal']) &
            (df['macd'].shift(1) <= df['macd_signal'].shift(1))
        )

        return df

    @staticmethod
    def calculate_rsi(df: pd.DataFrame, period: int = 14) -> pd.DataFrame:
        """Calculate RSI indicator"""
        # Calculate price changes
        delta = df['close'].diff()

        # Separate gains and losses
        gain = delta.where(delta > 0, 0)
        loss = -delta.where(delta < 0, 0)

        # Calculate average gain and loss
        avg_gain = gain.rolling(window=period).mean()
        avg_loss = loss.rolling(window=period).mean()

        # Calculate RS and RSI
        rs = avg_gain / avg_loss
        df['rsi'] = 100 - (100 / (1 + rs))

        return df

    @staticmethod
    def calculate_bollinger_bands(df: pd.DataFrame, period: int = 20, std_dev: int = 2) -> pd.DataFrame:
        """Calculate Bollinger Bands"""
        # Middle band (SMA)
        df['bb_middle'] = df['close'].rolling(window=period).mean()

        # Standard deviation
        rolling_std = df['close'].rolling(window=period).std()

        # Upper and lower bands
        df['bb_upper'] = df['bb_middle'] + (rolling_std * std_dev)
        df['bb_lower'] = df['bb_middle'] - (rolling_std * std_dev)

        return df

    @staticmethod
    def calculate_volume_indicators(df: pd.DataFrame) -> pd.DataFrame:
        """Calculate volume-based indicators"""
        df['volume_sma_20'] = df['volume'].rolling(window=20).mean()
        df['volume_surge'] = df['volume'] > (df['volume_sma_20'] * 1.5)

        return df

    @staticmethod
    def calculate_atr(df: pd.DataFrame, period: int = 14) -> pd.DataFrame:
        """
        Calculate Average True Range (ATR) indicator

        ATR measures market volatility by calculating the average of true ranges.
        True Range = max(high - low, abs(high - prev_close), abs(low - prev_close))

        Args:
            df: DataFrame with OHLCV data
            period: ATR period (default 14)

        Returns:
            DataFrame with 'atr' and 'atr_pct' columns added
        """
        if df.empty or len(df) < period + 1:
            df['atr'] = np.nan
            df['atr_pct'] = np.nan
            return df

        # Calculate True Range components
        high_low = df['high'] - df['low']
        high_prev_close = abs(df['high'] - df['close'].shift(1))
        low_prev_close = abs(df['low'] - df['close'].shift(1))

        # True Range is the maximum of the three
        true_range = pd.concat([high_low, high_prev_close, low_prev_close], axis=1).max(axis=1)

        # ATR is the exponential moving average of True Range
        df['atr'] = true_range.ewm(span=period, adjust=False).mean()

        # ATR as percentage of price (useful for comparison across different price levels)
        df['atr_pct'] = (df['atr'] / df['close']) * 100

        return df

    @staticmethod
    def get_current_atr(df: pd.DataFrame) -> tuple:
        """
        Get current ATR value and percentage

        Returns:
            (atr_value, atr_pct) or (None, None) if not available
        """
        if df.empty or 'atr' not in df.columns:
            return None, None

        latest = df.iloc[-1]
        atr_value = latest['atr'] if pd.notna(latest['atr']) else None
        atr_pct = latest['atr_pct'] if pd.notna(latest['atr_pct']) else None

        return atr_value, atr_pct

    @staticmethod
    def calculate_all_indicators(df: pd.DataFrame) -> pd.DataFrame:
        """Calculate all technical indicators"""
        if df.empty or len(df) < 200:
            return df

        df = IndicatorService.calculate_moving_averages(df)
        df = IndicatorService.calculate_macd(df)
        df = IndicatorService.calculate_rsi(df)
        df = IndicatorService.calculate_bollinger_bands(df)
        df = IndicatorService.calculate_volume_indicators(df)
        df = IndicatorService.calculate_atr(df)

        return df

    @staticmethod
    def check_price_above_sma(df: pd.DataFrame) -> bool:
        """Check if price is above SMA 20"""
        if df.empty or 'sma_20' not in df.columns:
            return False

        latest = df.iloc[-1]
        return latest['close'] > latest['sma_20'] if pd.notna(latest['sma_20']) else False

    @staticmethod
    def check_price_above_all_ema(df: pd.DataFrame) -> bool:
        """Check if price is above all EMA lines (7, 14, 30, 52)"""
        if df.empty:
            return False

        latest = df.iloc[-1]
        ema_columns = ['ema_7', 'ema_14', 'ema_30', 'ema_52']

        # Check if all EMA values exist and price is above them
        for col in ema_columns:
            if col not in df.columns or pd.isna(latest[col]):
                return False
            if latest['close'] <= latest[col]:
                return False

        return True

    @staticmethod
    def check_macd_golden_cross(df: pd.DataFrame) -> bool:
        """Check if MACD has golden cross"""
        if df.empty or 'macd_golden_cross' not in df.columns:
            return False

        # Check last few candles for golden cross
        return df['macd_golden_cross'].iloc[-3:].any()

    @staticmethod
    def detect_price_anomaly(
        df: pd.DataFrame,
        threshold: float = 2.0
    ) -> Tuple[bool, float]:
        """
        Detect price anomaly (sudden price change)

        Args:
            df: DataFrame with OHLCV data
            threshold: Price change percentage threshold

        Returns:
            (is_anomaly, price_change_pct)
        """
        if df.empty or len(df) < 2:
            return False, 0.0

        # Calculate price change percentage
        current_price = df['close'].iloc[-1]
        previous_price = df['close'].iloc[-2]
        price_change_pct = ((current_price - previous_price) / previous_price) * 100

        is_anomaly = abs(price_change_pct) >= threshold

        return is_anomaly, price_change_pct

    @staticmethod
    def calculate_price_changes(df: pd.DataFrame) -> Dict[str, float]:
        """Calculate price changes for different periods"""
        if df.empty:
            return {
                'change_1': 0,
                'change_5': 0,
                'change_10': 0,
                'change_20': 0,
            }

        current_price = df['close'].iloc[-1]
        changes = {}

        for period, label in [(1, 'change_1'), (5, 'change_5'),
                              (10, 'change_10'), (20, 'change_20')]:
            if len(df) > period:
                old_price = df['close'].iloc[-period - 1]
                changes[label] = ((current_price - old_price) / old_price) * 100
            else:
                changes[label] = 0

        return changes

    @staticmethod
    def calculate_technical_score(df: pd.DataFrame) -> float:
        """
        Calculate overall technical score (0-100)

        Scoring criteria:
        - Price above SMA: +20
        - MACD golden cross: +20
        - Price above all EMAs: +20
        - RSI between 40-70: +20
        - Volume surge: +20
        """
        if df.empty:
            return 0

        score = 0
        latest = df.iloc[-1]

        # Price above SMA 20
        if IndicatorService.check_price_above_sma(df):
            score += 20

        # MACD golden cross
        if IndicatorService.check_macd_golden_cross(df):
            score += 20

        # Price above all EMAs
        if IndicatorService.check_price_above_all_ema(df):
            score += 20

        # RSI in healthy range (not overbought/oversold)
        if 'rsi' in df.columns and pd.notna(latest['rsi']):
            if 40 <= latest['rsi'] <= 70:
                score += 20

        # Volume surge
        if 'volume_surge' in df.columns and latest['volume_surge']:
            score += 20

        return score

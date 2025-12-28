import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
from typing import List, Optional
from datetime import datetime
import os


class ChartService:
    """Service for generating K-line charts with indicators"""

    def __init__(self):
        self.chart_dir = "./charts"
        os.makedirs(self.chart_dir, exist_ok=True)

    def create_kline_chart(
        self,
        df: pd.DataFrame,
        symbol: str,
        timeframe: str,
        anomaly_points: Optional[List[int]] = None,
        show_volume: bool = True,
        show_indicators: bool = True
    ) -> str:
        """
        Create K-line chart with indicators and anomaly markers

        Args:
            df: DataFrame with OHLCV data and indicators
            symbol: Trading symbol
            timeframe: Timeframe
            anomaly_points: List of indices where anomalies occurred
            show_volume: Whether to show volume subplot
            show_indicators: Whether to show technical indicators

        Returns:
            Path to saved chart image
        """
        if df.empty:
            return ""

        # Create subplots
        rows = 1
        row_heights = [0.7]
        subplot_titles = [f"{symbol} - {timeframe}"]

        if show_volume:
            rows += 1
            row_heights.append(0.3)
            subplot_titles.append("Volume")

        fig = make_subplots(
            rows=rows,
            cols=1,
            shared_xaxes=True,
            vertical_spacing=0.03,
            row_heights=row_heights,
            subplot_titles=subplot_titles
        )

        # Add candlestick chart
        fig.add_trace(
            go.Candlestick(
                x=df['timestamp'],
                open=df['open'],
                high=df['high'],
                low=df['low'],
                close=df['close'],
                name='Price',
                increasing_line_color='#26a69a',
                decreasing_line_color='#ef5350'
            ),
            row=1, col=1
        )

        # Add technical indicators
        if show_indicators:
            # SMA
            if 'sma_20' in df.columns:
                fig.add_trace(
                    go.Scatter(
                        x=df['timestamp'],
                        y=df['sma_20'],
                        name='SMA 20',
                        line=dict(color='orange', width=1)
                    ),
                    row=1, col=1
                )

            # EMAs
            ema_colors = {
                'ema_7': '#00ff00',
                'ema_14': '#0000ff',
                'ema_30': '#ff00ff',
                'ema_52': '#ffff00'
            }

            for ema, color in ema_colors.items():
                if ema in df.columns:
                    fig.add_trace(
                        go.Scatter(
                            x=df['timestamp'],
                            y=df[ema],
                            name=ema.upper(),
                            line=dict(color=color, width=1, dash='dot')
                        ),
                        row=1, col=1
                    )

            # Bollinger Bands
            if all(col in df.columns for col in ['bb_upper', 'bb_middle', 'bb_lower']):
                fig.add_trace(
                    go.Scatter(
                        x=df['timestamp'],
                        y=df['bb_upper'],
                        name='BB Upper',
                        line=dict(color='gray', width=1, dash='dash'),
                        showlegend=False
                    ),
                    row=1, col=1
                )

                fig.add_trace(
                    go.Scatter(
                        x=df['timestamp'],
                        y=df['bb_lower'],
                        name='BB Lower',
                        line=dict(color='gray', width=1, dash='dash'),
                        fill='tonexty',
                        fillcolor='rgba(128, 128, 128, 0.1)',
                        showlegend=False
                    ),
                    row=1, col=1
                )

        # Mark anomaly points
        if anomaly_points:
            anomaly_data = df.iloc[anomaly_points]
            fig.add_trace(
                go.Scatter(
                    x=anomaly_data['timestamp'],
                    y=anomaly_data['high'] * 1.02,
                    mode='markers',
                    name='Anomaly',
                    marker=dict(
                        symbol='triangle-down',
                        size=15,
                        color='red',
                        line=dict(color='darkred', width=2)
                    )
                ),
                row=1, col=1
            )

        # Add volume bars
        if show_volume:
            colors = ['red' if close < open else 'green'
                     for close, open in zip(df['close'], df['open'])]

            fig.add_trace(
                go.Bar(
                    x=df['timestamp'],
                    y=df['volume'],
                    name='Volume',
                    marker_color=colors,
                    showlegend=False
                ),
                row=2 if rows > 1 else 1,
                col=1
            )

            # Volume SMA
            if 'volume_sma_20' in df.columns:
                fig.add_trace(
                    go.Scatter(
                        x=df['timestamp'],
                        y=df['volume_sma_20'],
                        name='Volume SMA 20',
                        line=dict(color='orange', width=2),
                        showlegend=False
                    ),
                    row=2 if rows > 1 else 1,
                    col=1
                )

        # Update layout
        fig.update_layout(
            title=f"{symbol} - {timeframe} Chart",
            xaxis_title="Time",
            yaxis_title="Price (USDT)",
            template="plotly_dark",
            height=800 if show_volume else 600,
            hovermode='x unified',
            xaxis_rangeslider_visible=False
        )

        # Save chart
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{symbol.replace('/', '_')}_{timeframe}_{timestamp}.png"
        filepath = os.path.join(self.chart_dir, filename)

        fig.write_image(filepath, width=1400, height=800 if show_volume else 600)

        return filepath

    def create_macd_chart(self, df: pd.DataFrame, symbol: str) -> str:
        """Create MACD indicator chart"""
        if df.empty or 'macd' not in df.columns:
            return ""

        fig = go.Figure()

        # MACD line
        fig.add_trace(
            go.Scatter(
                x=df['timestamp'],
                y=df['macd'],
                name='MACD',
                line=dict(color='blue', width=2)
            )
        )

        # Signal line
        fig.add_trace(
            go.Scatter(
                x=df['timestamp'],
                y=df['macd_signal'],
                name='Signal',
                line=dict(color='orange', width=2)
            )
        )

        # Histogram
        colors = ['green' if val >= 0 else 'red' for val in df['macd_histogram']]
        fig.add_trace(
            go.Bar(
                x=df['timestamp'],
                y=df['macd_histogram'],
                name='Histogram',
                marker_color=colors
            )
        )

        # Mark golden crosses
        if 'macd_golden_cross' in df.columns:
            golden_cross_data = df[df['macd_golden_cross']]
            if not golden_cross_data.empty:
                fig.add_trace(
                    go.Scatter(
                        x=golden_cross_data['timestamp'],
                        y=golden_cross_data['macd'],
                        mode='markers',
                        name='Golden Cross',
                        marker=dict(symbol='star', size=15, color='gold')
                    )
                )

        fig.update_layout(
            title=f"{symbol} - MACD Indicator",
            xaxis_title="Time",
            yaxis_title="MACD",
            template="plotly_dark",
            height=400,
            hovermode='x unified'
        )

        # Save chart
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{symbol.replace('/', '_')}_MACD_{timestamp}.png"
        filepath = os.path.join(self.chart_dir, filename)

        fig.write_image(filepath, width=1400, height=400)

        return filepath

    def create_multi_timeframe_chart(
        self,
        dfs: dict,
        symbol: str
    ) -> str:
        """
        Create multi-timeframe comparison chart

        Args:
            dfs: Dictionary of {timeframe: DataFrame}
            symbol: Trading symbol

        Returns:
            Path to saved chart
        """
        timeframes = list(dfs.keys())
        rows = len(timeframes)

        fig = make_subplots(
            rows=rows,
            cols=1,
            shared_xaxes=False,
            vertical_spacing=0.05,
            subplot_titles=[f"{symbol} - {tf}" for tf in timeframes]
        )

        for idx, (tf, df) in enumerate(dfs.items(), start=1):
            if df.empty:
                continue

            # Add candlestick
            fig.add_trace(
                go.Candlestick(
                    x=df['timestamp'],
                    open=df['open'],
                    high=df['high'],
                    low=df['low'],
                    close=df['close'],
                    name=tf,
                    increasing_line_color='#26a69a',
                    decreasing_line_color='#ef5350',
                    showlegend=False
                ),
                row=idx, col=1
            )

            # Add SMA if available
            if 'sma_20' in df.columns:
                fig.add_trace(
                    go.Scatter(
                        x=df['timestamp'],
                        y=df['sma_20'],
                        name=f'SMA 20 ({tf})',
                        line=dict(color='orange', width=1),
                        showlegend=False
                    ),
                    row=idx, col=1
                )

        fig.update_layout(
            title=f"{symbol} - Multi-Timeframe Analysis",
            template="plotly_dark",
            height=300 * rows,
            hovermode='x unified',
            xaxis_rangeslider_visible=False
        )

        # Save chart
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{symbol.replace('/', '_')}_multi_tf_{timestamp}.png"
        filepath = os.path.join(self.chart_dir, filename)

        fig.write_image(filepath, width=1400, height=300 * rows)

        return filepath

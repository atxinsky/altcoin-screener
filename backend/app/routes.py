from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime

from backend.database.database import get_db_session
from backend.services.binance_service import BinanceService
from backend.services.screening_service import ScreeningService
from backend.services.indicator_service import IndicatorService
from backend.services.chart_service import ChartService
from backend.services.notification_service import NotificationService
from backend.services.trading_service import TradingService
from backend.services.sim_trading_service import SimTradingService


router = APIRouter()


# Request/Response models
class ScreenRequest(BaseModel):
    timeframe: str = "5m"
    min_volume: Optional[float] = None
    min_price_change: Optional[float] = None
    send_notification: bool = False


class ChartRequest(BaseModel):
    symbol: str
    timeframe: str = "5m"
    show_indicators: bool = True


class MarketOrderRequest(BaseModel):
    symbol: str
    side: str  # 'BUY' or 'SELL'
    quantity: float
    notes: Optional[str] = None


class LimitOrderRequest(BaseModel):
    symbol: str
    side: str  # 'BUY' or 'SELL'
    quantity: float
    price: float
    notes: Optional[str] = None


class WatchlistRequest(BaseModel):
    symbol: str
    notes: Optional[str] = None


# Helper function to run async notifications in background
async def send_screening_notification(results: List[dict], timeframe: str, db: Session):
    """Background task to send notifications"""
    notification_service = NotificationService(db)
    await notification_service.send_screening_alert(
        results=results,
        timeframe=timeframe,
        send_email=True,
        send_telegram=True
    )


@router.get("/market-overview")
async def get_market_overview():
    """Get BTC and ETH market overview"""
    try:
        binance = BinanceService()
        overview = binance.get_market_overview()
        return overview
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/symbols")
async def get_symbols():
    """Get all altcoin symbols"""
    try:
        binance = BinanceService()
        symbols = binance.get_altcoins()
        return {"symbols": symbols, "count": len(symbols)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/screen")
async def screen_altcoins(
    request: ScreenRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db_session)
):
    """
    Screen altcoins based on criteria

    - **timeframe**: Time interval (5m, 15m, 1h, 4h)
    - **min_volume**: Minimum 24h volume in USD
    - **min_price_change**: Minimum price change percentage
    - **send_notification**: Whether to send notification
    """
    try:
        screening_service = ScreeningService(db)

        results = screening_service.screen_altcoins(
            timeframe=request.timeframe,
            min_volume=request.min_volume,
            min_price_change=request.min_price_change
        )

        # Send notification in background if requested
        if request.send_notification and results:
            background_tasks.add_task(
                send_screening_notification,
                results,
                request.timeframe,
                db
            )

        return {
            "success": True,
            "count": len(results),
            "results": results[:20],  # Return top 20
            "timestamp": datetime.utcnow().isoformat()
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/top-opportunities")
async def get_top_opportunities(
    limit: int = Query(20, ge=1, le=100),
    min_score: float = Query(60, ge=0, le=100),
    db: Session = Depends(get_db_session)
):
    """Get top opportunities from latest screening"""
    try:
        screening_service = ScreeningService(db)
        results = screening_service.get_top_opportunities(
            limit=limit,
            min_score=min_score
        )

        return {
            "success": True,
            "count": len(results),
            "results": results
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/chart")
async def generate_chart(
    request: ChartRequest,
    db: Session = Depends(get_db_session)
):
    """Generate K-line chart for a symbol"""
    try:
        binance = BinanceService()
        chart_service = ChartService()
        indicator_service = IndicatorService()

        # 先验证symbol是否是活跃的USDT现货交易对
        active_symbols = binance.get_all_spot_symbols()
        if request.symbol not in active_symbols:
            raise HTTPException(
                status_code=404,
                detail=f"{request.symbol} 不是币安活跃的USDT现货交易对，可能已下架或不存在"
            )

        # Fetch data
        df = binance.fetch_ohlcv(
            symbol=request.symbol,
            timeframe=request.timeframe,
            limit=500
        )

        if df.empty:
            raise HTTPException(
                status_code=404,
                detail=f"{request.symbol} 无法获取K线数据，请检查交易对是否正确"
            )

        # Calculate indicators
        df = indicator_service.calculate_all_indicators(df)

        # Detect anomalies
        anomaly_points = []
        for i in range(len(df)):
            if i > 0:
                subset = df.iloc[:i+1]
                is_anomaly, _ = indicator_service.detect_price_anomaly(subset)
                if is_anomaly:
                    anomaly_points.append(i)

        # Generate chart
        chart_path = chart_service.create_kline_chart(
            df=df,
            symbol=request.symbol,
            timeframe=request.timeframe,
            anomaly_points=anomaly_points,
            show_indicators=request.show_indicators
        )

        return {
            "success": True,
            "chart_url": f"/charts/{chart_path.split('/')[-1]}",
            "anomaly_count": len(anomaly_points)
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/historical")
async def get_historical_data(
    symbol: str = Query(..., description="Trading pair symbol"),
    timeframe: str = Query("5m"),
    days: int = Query(7, ge=1, le=30)
):
    """Get historical OHLCV data for a symbol"""
    try:
        binance = BinanceService()

        # 直接获取历史数据，不先验证symbol（避免API权限问题）
        df = binance.get_historical_data(
            symbol=symbol,
            timeframe=timeframe,
            days=days
        )

        if df is None or df.empty:
            raise HTTPException(
                status_code=404,
                detail=f"{symbol} 无法获取历史数据，请检查交易对是否正确"
            )

        # Convert to dict
        data = df.to_dict(orient='records')

        # Convert timestamps to ISO format
        for record in data:
            if 'timestamp' in record:
                record['timestamp'] = record['timestamp'].isoformat()

        return {
            "success": True,
            "symbol": symbol,
            "timeframe": timeframe,
            "count": len(data),
            "data": data
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/indicators")
async def get_indicators(
    symbol: str = Query(..., description="Trading pair symbol"),
    timeframe: str = Query("5m")
):
    """Get technical indicators for a symbol"""
    try:
        binance = BinanceService()
        indicator_service = IndicatorService()

        # 直接获取数据，不先验证symbol（避免API权限问题）
        df = binance.fetch_ohlcv(symbol, timeframe, limit=500)

        if df.empty:
            raise HTTPException(
                status_code=404,
                detail=f"{symbol} 无法获取数据，请检查交易对是否正确"
            )

        # Calculate indicators
        df = indicator_service.calculate_all_indicators(df)

        # Get latest values
        latest = df.iloc[-1]

        indicators = {
            'symbol': symbol,
            'timeframe': timeframe,
            'timestamp': latest['timestamp'].isoformat(),
            'price': float(latest['close']),
            'sma_20': float(latest.get('sma_20')) if latest.get('sma_20') is not None else None,
            'ema_7': float(latest.get('ema_7')) if latest.get('ema_7') is not None else None,
            'ema_14': float(latest.get('ema_14')) if latest.get('ema_14') is not None else None,
            'ema_30': float(latest.get('ema_30')) if latest.get('ema_30') is not None else None,
            'ema_52': float(latest.get('ema_52')) if latest.get('ema_52') is not None else None,
            'macd': float(latest.get('macd')) if latest.get('macd') is not None else None,
            'macd_signal': float(latest.get('macd_signal')) if latest.get('macd_signal') is not None else None,
            'macd_histogram': float(latest.get('macd_histogram')) if latest.get('macd_histogram') is not None else None,
            'rsi': float(latest.get('rsi')) if latest.get('rsi') is not None else None,
            'bb_upper': float(latest.get('bb_upper')) if latest.get('bb_upper') is not None else None,
            'bb_middle': float(latest.get('bb_middle')) if latest.get('bb_middle') is not None else None,
            'bb_lower': float(latest.get('bb_lower')) if latest.get('bb_lower') is not None else None,
            'volume_sma_20': float(latest.get('volume_sma_20')) if latest.get('volume_sma_20') is not None else None,
            'above_sma': bool(indicator_service.check_price_above_sma(df)),
            'macd_golden_cross': bool(indicator_service.check_macd_golden_cross(df)),
            'above_all_ema': bool(indicator_service.check_price_above_all_ema(df)),
            'technical_score': float(indicator_service.calculate_technical_score(df)),
        }

        return {
            "success": True,
            "indicators": indicators,
            "anomaly_count": 0  # Placeholder for anomaly detection
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats")
async def get_stats(db: Session = Depends(get_db_session)):
    """Get database statistics"""
    try:
        from backend.database.models import KlineData, ScreeningResult, Alert

        kline_count = db.query(KlineData).count()
        screening_count = db.query(ScreeningResult).count()
        alert_count = db.query(Alert).count()

        # Get latest screening
        latest_screening = db.query(ScreeningResult).order_by(
            ScreeningResult.timestamp.desc()
        ).first()

        return {
            "success": True,
            "stats": {
                "total_klines": kline_count,
                "total_screenings": screening_count,
                "total_alerts": alert_count,
                "latest_screening": latest_screening.timestamp.isoformat() if latest_screening else None
            }
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== Historical Rankings ====================

@router.get("/history/rankings")
async def get_historical_rankings(
    days: int = Query(3, ge=1, le=30),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db_session)
):
    """
    Get top symbols ranked by average score over the past N days

    - **days**: Number of days to look back (default 3)
    - **limit**: Number of top symbols to return (default 20)
    """
    try:
        from backend.database.models import ScreeningResult
        from datetime import datetime, timedelta
        from sqlalchemy import func

        # 获取当前币安现货市场的所有USDT交易对
        try:
            binance = BinanceService()
            active_symbols = set(binance.get_all_spot_symbols())
            print(f"获取到 {len(active_symbols)} 个活跃的USDT交易对")
        except Exception as e:
            print(f"获取币安交易对失败: {e}")
            import traceback
            traceback.print_exc()
            # 如果获取失败，返回空集合，这样会过滤掉所有币种（安全起见）
            active_symbols = set()

        # Calculate the cutoff date
        cutoff_date = datetime.utcnow() - timedelta(days=days)

        # Query to get average score per symbol over the past N days
        results = db.query(
            ScreeningResult.symbol,
            func.avg(ScreeningResult.total_score).label('avg_score'),
            func.max(ScreeningResult.total_score).label('max_score'),
            func.min(ScreeningResult.total_score).label('min_score'),
            func.count(ScreeningResult.id).label('appearance_count'),
            func.max(ScreeningResult.timestamp).label('last_seen')
        ).filter(
            ScreeningResult.timestamp >= cutoff_date
        ).group_by(
            ScreeningResult.symbol
        ).order_by(
            func.avg(ScreeningResult.total_score).desc()
        ).all()

        # 只保留当前在币安现货市场存在的币种
        rankings = []
        rank = 1
        for row in results:
            if row.symbol in active_symbols:
                rankings.append({
                    'rank': rank,
                    'symbol': row.symbol,
                    'avg_score': round(row.avg_score, 2),
                    'max_score': round(row.max_score, 2),
                    'min_score': round(row.min_score, 2),
                    'appearance_count': row.appearance_count,
                    'last_seen': row.last_seen.isoformat()
                })
                rank += 1
                if rank > limit:
                    break

        return {
            "success": True,
            "days": days,
            "count": len(rankings),
            "rankings": rankings
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/history/symbol")
async def get_symbol_history(
    symbol: str = Query(..., description="Trading pair symbol"),
    days: int = Query(7, ge=1, le=30),
    db: Session = Depends(get_db_session)
):
    """
    Get historical scores for a specific symbol

    - **symbol**: Trading pair symbol (query parameter)
    - **days**: Number of days to look back (default 7)
    """
    try:
        from backend.database.models import ScreeningResult
        from datetime import datetime, timedelta

        cutoff_date = datetime.utcnow() - timedelta(days=days)

        results = db.query(ScreeningResult).filter(
            ScreeningResult.symbol == symbol,
            ScreeningResult.timestamp >= cutoff_date
        ).order_by(
            ScreeningResult.timestamp.desc()
        ).all()

        history = []
        for r in results:
            history.append({
                'timestamp': r.timestamp.isoformat(),
                'total_score': r.total_score,
                'beta_score': r.beta_score,
                'volume_score': r.volume_score,
                'technical_score': r.technical_score,
                'current_price': r.current_price,
                'volume_24h': r.volume_24h,
                'btc_ratio_change_pct': r.btc_ratio_change_pct,
                'eth_ratio_change_pct': r.eth_ratio_change_pct
            })

        return {
            "success": True,
            "symbol": symbol,
            "days": days,
            "count": len(history),
            "history": history
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/history/recent")
async def get_recent_screenings(
    hours: int = Query(24, ge=1, le=168),
    min_score: float = Query(0, ge=0, le=100),
    db: Session = Depends(get_db_session)
):
    """
    Get all screening results from the past N hours

    - **hours**: Number of hours to look back (default 24)
    - **min_score**: Minimum score filter (default 0)
    """
    try:
        from backend.database.models import ScreeningResult
        from datetime import datetime, timedelta

        cutoff_date = datetime.utcnow() - timedelta(hours=hours)

        results = db.query(ScreeningResult).filter(
            ScreeningResult.timestamp >= cutoff_date,
            ScreeningResult.total_score >= min_score
        ).order_by(
            ScreeningResult.timestamp.desc(),
            ScreeningResult.total_score.desc()
        ).all()

        screenings = []
        for r in results:
            screenings.append({
                'id': r.id,
                'symbol': r.symbol,
                'timestamp': r.timestamp.isoformat(),
                'timeframe': r.timeframe,
                'total_score': r.total_score,
                'beta_score': r.beta_score,
                'volume_score': r.volume_score,
                'technical_score': r.technical_score,
                'current_price': r.current_price,
                'btc_ratio_change_pct': r.btc_ratio_change_pct,
                'eth_ratio_change_pct': r.eth_ratio_change_pct,
                'volume_24h': r.volume_24h,
                'above_sma': r.above_sma,
                'macd_golden_cross': r.macd_golden_cross,
                'above_all_ema': r.above_all_ema,
                'volume_surge': r.volume_surge,
                'price_anomaly': r.price_anomaly
            })

        return {
            "success": True,
            "hours": hours,
            "count": len(screenings),
            "screenings": screenings
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== Trading Endpoints ====================

@router.post("/trade/market")
async def create_market_order(
    request: MarketOrderRequest,
    db: Session = Depends(get_db_session)
):
    """
    Create a market order

    - **symbol**: Trading pair (e.g., 'BTC/USDT')
    - **side**: 'BUY' or 'SELL'
    - **quantity**: Amount to buy/sell
    - **notes**: Optional notes
    """
    try:
        trading_service = TradingService(db)
        result = trading_service.create_market_order(
            symbol=request.symbol,
            side=request.side,
            quantity=request.quantity,
            notes=request.notes
        )

        return {
            "success": True,
            "order": result
        }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        import traceback
        error_detail = f"{str(e)}\n\nTraceback:\n{traceback.format_exc()}"
        print(f"Order creation error: {error_detail}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/trade/limit")
async def create_limit_order(
    request: LimitOrderRequest,
    db: Session = Depends(get_db_session)
):
    """
    Create a limit order

    - **symbol**: Trading pair (e.g., 'BTC/USDT')
    - **side**: 'BUY' or 'SELL'
    - **quantity**: Amount to buy/sell
    - **price**: Limit price
    - **notes**: Optional notes
    """
    try:
        trading_service = TradingService(db)
        result = trading_service.create_limit_order(
            symbol=request.symbol,
            side=request.side,
            quantity=request.quantity,
            price=request.price,
            notes=request.notes
        )

        return {
            "success": True,
            "order": result
        }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/trade/{order_id}")
async def cancel_order(
    order_id: int,
    db: Session = Depends(get_db_session)
):
    """Cancel an open order"""
    try:
        trading_service = TradingService(db)
        result = trading_service.cancel_order(order_id)

        return {
            "success": True,
            "order": result
        }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/trade/history")
async def get_order_history(
    symbol: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db_session)
):
    """
    Get order history

    - **symbol**: Optional filter by trading pair
    - **limit**: Number of orders to return (default 50, max 200)
    """
    try:
        trading_service = TradingService(db)
        orders = trading_service.get_order_history(
            symbol=symbol,
            limit=limit
        )

        return {
            "success": True,
            "count": len(orders),
            "orders": orders
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/trade/balance")
async def get_balance(
    asset: str = Query("USDT"),
    db: Session = Depends(get_db_session)
):
    """
    Get account balance for a specific asset

    - **asset**: Asset symbol (default 'USDT')
    """
    try:
        trading_service = TradingService(db)
        balance = trading_service.get_balance(asset=asset)

        return {
            "success": True,
            "balance": balance
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/trade/balances")
async def get_all_balances(db: Session = Depends(get_db_session)):
    """Get all non-zero account balances"""
    try:
        trading_service = TradingService(db)
        balances = trading_service.get_all_balances()

        return {
            "success": True,
            "count": len(balances),
            "balances": balances
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== Watchlist Endpoints ====================

@router.post("/watchlist")
async def add_to_watchlist(
    request: WatchlistRequest,
    db: Session = Depends(get_db_session)
):
    """
    Add a symbol to watchlist

    - **symbol**: Trading pair to add
    - **notes**: Optional notes
    """
    try:
        trading_service = TradingService(db)
        result = trading_service.add_to_watchlist(
            symbol=request.symbol,
            notes=request.notes
        )

        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/watchlist")
async def get_watchlist(db: Session = Depends(get_db_session)):
    """Get all watchlist symbols"""
    try:
        trading_service = TradingService(db)
        watchlist = trading_service.get_watchlist()

        return {
            "success": True,
            "count": len(watchlist),
            "watchlist": watchlist
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/watchlist/{symbol}")
async def remove_from_watchlist(
    symbol: str,
    db: Session = Depends(get_db_session)
):
    """Remove a symbol from watchlist"""
    try:
        trading_service = TradingService(db)
        result = trading_service.remove_from_watchlist(symbol=symbol)

        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/top-gainers")
async def get_top_gainers(
    timeframe: str = Query("5m", description="Timeframe (5m, 15m, 1h)"),
    limit: int = Query(20, ge=1, le=100)
):
    """Get top gainers by price change percentage for specified timeframe"""
    try:
        binance = BinanceService()

        # Get all USDT pairs
        symbols = binance.get_all_spot_symbols()
        if not symbols:
            return {"success": True, "count": 0, "results": []}

        gainers = []

        # 根据时间周期计算需要获取多少根K线
        candle_count_map = {
            '5m': 2,    # 当前 + 前一根
            '15m': 2,
            '1h': 2,
            '4h': 2
        }
        candle_count = candle_count_map.get(timeframe, 2)

        for symbol in symbols[:200]:  # Limit to first 200 symbols to avoid timeout
            try:
                # 获取K线数据来计算指定时间周期的涨幅
                df = binance.fetch_ohlcv(symbol, timeframe, limit=candle_count)

                if df.empty or len(df) < 2:
                    continue

                # 计算涨幅：(当前收盘价 - 前一根收盘价) / 前一根收盘价 * 100
                current_close = df['close'].iloc[-1]
                previous_close = df['close'].iloc[-2]
                price_change_pct = ((current_close - previous_close) / previous_close) * 100

                # 获取当前ticker用于成交量等信息
                ticker = binance.fetch_ticker(symbol)
                if not ticker:
                    continue

                gainers.append({
                    'symbol': symbol,
                    'timeframe': timeframe,
                    'current_price': float(current_close),
                    'price_change_pct': float(price_change_pct),
                    'volume_24h': float(ticker.get('quoteVolume', 0)),
                    'high_24h': float(ticker.get('high', 0)),
                    'low_24h': float(ticker.get('low', 0))
                })
            except Exception as e:
                print(f"Error fetching {symbol}: {e}")
                continue

        # Sort by price change percentage
        gainers.sort(key=lambda x: x['price_change_pct'], reverse=True)

        # Take top N
        top_gainers = gainers[:limit]

        return {
            "success": True,
            "count": len(top_gainers),
            "results": top_gainers
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== Simulated Trading Endpoints ====================

class CreateSimAccountRequest(BaseModel):
    account_name: str
    initial_balance: float = 10000.0
    max_positions: int = 5
    position_size_pct: float = 2.0
    entry_score_min: float = 75.0
    entry_technical_min: float = 60.0
    stop_loss_pct: float = 3.0
    take_profit_levels: List[float] = [6.0, 9.0, 12.0]


class UpdateSimAccountRequest(BaseModel):
    auto_trading_enabled: Optional[bool] = None
    max_positions: Optional[int] = None
    position_size_pct: Optional[float] = None
    entry_score_min: Optional[float] = None
    entry_technical_min: Optional[float] = None
    stop_loss_pct: Optional[float] = None
    take_profit_levels: Optional[List[float]] = None


class OpenPositionRequest(BaseModel):
    symbol: str
    entry_price: Optional[float] = None  # If None, use current market price


class ClosePositionRequest(BaseModel):
    close_price: Optional[float] = None  # If None, use current market price
    close_reason: str = 'MANUAL'
    partial_pct: float = 100.0


@router.post("/sim-trading/accounts")
async def create_sim_account(
    request: CreateSimAccountRequest,
    db: Session = Depends(get_db_session)
):
    """
    Create a new simulated trading account

    - **account_name**: Name for the account
    - **initial_balance**: Starting balance (default 10000 USDT)
    - **max_positions**: Maximum number of concurrent positions (default 5)
    - **position_size_pct**: Position size as % of equity (default 2%)
    - **entry_score_min**: Minimum total score to enter (default 75)
    - **entry_technical_min**: Minimum technical score (default 60)
    - **stop_loss_pct**: Stop loss percentage (default 3%)
    - **take_profit_levels**: Take profit levels (default [6, 9, 12])
    """
    try:
        sim_trading = SimTradingService(db)
        account = sim_trading.create_account(
            account_name=request.account_name,
            initial_balance=request.initial_balance,
            max_positions=request.max_positions,
            position_size_pct=request.position_size_pct,
            entry_score_min=request.entry_score_min,
            entry_technical_min=request.entry_technical_min,
            stop_loss_pct=request.stop_loss_pct,
            take_profit_levels=request.take_profit_levels
        )

        return {
            "success": True,
            "account": {
                "id": account.id,
                "account_name": account.account_name,
                "initial_balance": account.initial_balance,
                "current_balance": account.current_balance,
                "total_equity": account.total_equity,
                "created_at": account.created_at.isoformat()
            }
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sim-trading/accounts")
async def get_sim_accounts(db: Session = Depends(get_db_session)):
    """Get all simulated trading accounts"""
    try:
        sim_trading = SimTradingService(db)
        accounts = sim_trading.get_all_accounts()

        return {
            "success": True,
            "count": len(accounts),
            "accounts": [{
                "id": acc.id,
                "account_name": acc.account_name,
                "initial_balance": acc.initial_balance,
                "total_equity": acc.total_equity,
                "total_pnl": acc.total_pnl,
                "total_trades": acc.total_trades,
                "win_rate": (acc.winning_trades / (acc.winning_trades + acc.losing_trades) * 100)
                    if (acc.winning_trades + acc.losing_trades) > 0 else 0,
                "auto_trading_enabled": acc.auto_trading_enabled,
                "is_active": acc.is_active,
                "created_at": acc.created_at.isoformat()
            } for acc in accounts]
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sim-trading/accounts/{account_id}")
async def get_sim_account_summary(
    account_id: int,
    db: Session = Depends(get_db_session)
):
    """Get detailed summary of a simulated trading account"""
    try:
        sim_trading = SimTradingService(db)
        summary = sim_trading.get_account_summary(account_id)

        if not summary:
            raise HTTPException(status_code=404, detail="Account not found")

        return {
            "success": True,
            "summary": summary
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/sim-trading/accounts/{account_id}")
async def update_sim_account(
    account_id: int,
    request: UpdateSimAccountRequest,
    db: Session = Depends(get_db_session)
):
    """Update simulated trading account settings"""
    try:
        sim_trading = SimTradingService(db)
        account = sim_trading.get_account(account_id)

        if not account:
            raise HTTPException(status_code=404, detail="Account not found")

        # Update fields
        if request.auto_trading_enabled is not None:
            account.auto_trading_enabled = request.auto_trading_enabled
        if request.max_positions is not None:
            account.max_positions = request.max_positions
        if request.position_size_pct is not None:
            account.position_size_pct = request.position_size_pct
        if request.entry_score_min is not None:
            account.entry_score_min = request.entry_score_min
        if request.entry_technical_min is not None:
            account.entry_technical_min = request.entry_technical_min
        if request.stop_loss_pct is not None:
            account.stop_loss_pct = request.stop_loss_pct
        if request.take_profit_levels is not None:
            account.take_profit_levels = request.take_profit_levels

        account.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(account)

        return {
            "success": True,
            "message": "Account updated successfully",
            "account_id": account.id,
            "auto_trading_enabled": account.auto_trading_enabled
        }

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/sim-trading/accounts/{account_id}")
async def delete_sim_account(
    account_id: int,
    db: Session = Depends(get_db_session)
):
    """
    Delete a simulated trading account and all related data

    This will permanently delete:
    - All positions (open and closed)
    - All trades
    - All auto-trading logs
    - The account itself
    """
    try:
        from backend.database.models import SimAccount, SimPosition, SimTrade, AutoTradingLog

        # Check if account exists
        account = db.query(SimAccount).filter(SimAccount.id == account_id).first()
        if not account:
            raise HTTPException(status_code=404, detail="Account not found")

        account_name = account.account_name

        # Delete all related data in order
        # 1. Delete auto trading logs
        logs_deleted = db.query(AutoTradingLog).filter(
            AutoTradingLog.account_id == account_id
        ).delete()

        # 2. Delete trades
        trades_deleted = db.query(SimTrade).filter(
            SimTrade.account_id == account_id
        ).delete()

        # 3. Delete positions
        positions_deleted = db.query(SimPosition).filter(
            SimPosition.account_id == account_id
        ).delete()

        # 4. Delete the account
        db.delete(account)
        db.commit()

        return {
            "success": True,
            "message": f"Account '{account_name}' deleted successfully",
            "deleted": {
                "account_id": account_id,
                "positions": positions_deleted,
                "trades": trades_deleted,
                "logs": logs_deleted
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/sim-trading/accounts/{account_id}/positions")
async def open_sim_position(
    account_id: int,
    request: OpenPositionRequest,
    db: Session = Depends(get_db_session)
):
    """Manually open a simulated position"""
    try:
        sim_trading = SimTradingService(db)

        # Get entry price
        entry_price = request.entry_price
        if entry_price is None:
            entry_price = sim_trading._get_current_price(request.symbol)
            if not entry_price:
                raise HTTPException(status_code=400, detail=f"Failed to get price for {request.symbol}")

        success, message, position = sim_trading.open_position(
            account_id=account_id,
            symbol=request.symbol,
            entry_price=entry_price
        )

        if not success:
            raise HTTPException(status_code=400, detail=message)

        return {
            "success": True,
            "message": message,
            "position": sim_trading._position_to_dict(position)
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/sim-trading/positions/{position_id}")
async def close_sim_position(
    position_id: int,
    request: ClosePositionRequest,
    db: Session = Depends(get_db_session)
):
    """Manually close a simulated position"""
    try:
        sim_trading = SimTradingService(db)

        success, message = sim_trading.close_position(
            position_id=position_id,
            close_price=request.close_price,
            close_reason=request.close_reason,
            partial_pct=request.partial_pct
        )

        if not success:
            raise HTTPException(status_code=400, detail=message)

        return {
            "success": True,
            "message": message
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sim-trading/accounts/{account_id}/positions")
async def get_sim_positions(
    account_id: int,
    include_closed: bool = Query(False),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db_session)
):
    """Get positions for a simulated account"""
    try:
        sim_trading = SimTradingService(db)

        if include_closed:
            positions = sim_trading.get_position_history(account_id, limit=limit)
        else:
            positions = sim_trading.get_open_positions(account_id)

        return {
            "success": True,
            "count": len(positions),
            "positions": [sim_trading._position_to_dict(p) for p in positions]
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sim-trading/accounts/{account_id}/trades")
async def get_sim_trades(
    account_id: int,
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db_session)
):
    """Get trade history for a simulated account"""
    try:
        from backend.database.models import SimTrade

        trades = db.query(SimTrade).filter(
            SimTrade.account_id == account_id
        ).order_by(SimTrade.trade_time.desc()).limit(limit).all()

        sim_trading = SimTradingService(db)

        return {
            "success": True,
            "count": len(trades),
            "trades": [sim_trading._trade_to_dict(t) for t in trades]
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/sim-trading/accounts/{account_id}/auto-trade")
async def trigger_auto_trading(
    account_id: int,
    db: Session = Depends(get_db_session)
):
    """
    Manually trigger auto-trading monitor for an account
    (Normally this runs on a schedule)
    """
    try:
        sim_trading = SimTradingService(db)
        actions = sim_trading.auto_trade_monitor(account_id)

        return {
            "success": True,
            "actions": actions
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/sim-trading/accounts/{account_id}/check-exits")
async def check_sim_exits(
    account_id: int,
    db: Session = Depends(get_db_session)
):
    """Check and execute stop-loss / take-profit for all positions"""
    try:
        sim_trading = SimTradingService(db)
        exits = sim_trading.check_and_execute_exits(account_id)

        return {
            "success": True,
            "exits_count": len(exits),
            "exits": exits
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sim-trading/accounts/{account_id}/logs")
async def get_sim_trading_logs(
    account_id: int,
    limit: int = Query(default=100, le=500),
    db: Session = Depends(get_db_session)
):
    """Get auto trading decision logs for an account"""
    try:
        from backend.database.models import AutoTradingLog

        logs = db.query(AutoTradingLog)\
            .filter(AutoTradingLog.account_id == account_id)\
            .order_by(AutoTradingLog.timestamp.desc())\
            .limit(limit)\
            .all()

        log_list = []
        for log in logs:
            log_list.append({
                "id": log.id,
                "action": log.action,
                "symbol": log.symbol,
                "reason": log.reason,
                "screening_score": log.screening_score,
                "success": log.success,
                "error_message": log.error_message,
                "timestamp": log.timestamp.isoformat() if log.timestamp else None
            })

        return {
            "success": True,
            "count": len(log_list),
            "logs": log_list
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== Notification Settings ====================

class NotificationSettingsRequest(BaseModel):
    email_enabled: Optional[bool] = None
    telegram_enabled: Optional[bool] = None
    min_interval_minutes: Optional[int] = None
    daily_limit: Optional[int] = None
    min_score_threshold: Optional[float] = None
    notify_top_n: Optional[int] = None
    notify_high_score: Optional[bool] = None
    notify_new_signals: Optional[bool] = None
    notify_position_updates: Optional[bool] = None
    quiet_hours_enabled: Optional[bool] = None
    quiet_hours_start: Optional[int] = None
    quiet_hours_end: Optional[int] = None


@router.get("/notification-settings")
async def get_notification_settings(
    db: Session = Depends(get_db_session)
):
    """Get notification settings"""
    try:
        from backend.database.models import NotificationSettings

        settings = db.query(NotificationSettings).first()

        # Create default settings if not exists
        if not settings:
            settings = NotificationSettings()
            db.add(settings)
            db.commit()
            db.refresh(settings)

        return {
            "success": True,
            "settings": {
                "id": settings.id,
                "email_enabled": settings.email_enabled,
                "telegram_enabled": settings.telegram_enabled,
                "min_interval_minutes": settings.min_interval_minutes,
                "daily_limit": settings.daily_limit,
                "daily_count": settings.daily_count,
                "min_score_threshold": settings.min_score_threshold,
                "notify_top_n": settings.notify_top_n,
                "notify_high_score": settings.notify_high_score,
                "notify_new_signals": settings.notify_new_signals,
                "notify_position_updates": settings.notify_position_updates,
                "quiet_hours_enabled": settings.quiet_hours_enabled,
                "quiet_hours_start": settings.quiet_hours_start,
                "quiet_hours_end": settings.quiet_hours_end,
                "last_notification_time": settings.last_notification_time.isoformat() if settings.last_notification_time else None,
                "updated_at": settings.updated_at.isoformat() if settings.updated_at else None
            }
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/notification-settings")
async def update_notification_settings(
    request: NotificationSettingsRequest,
    db: Session = Depends(get_db_session)
):
    """Update notification settings"""
    try:
        from backend.database.models import NotificationSettings

        settings = db.query(NotificationSettings).first()

        # Create default settings if not exists
        if not settings:
            settings = NotificationSettings()
            db.add(settings)
            db.commit()
            db.refresh(settings)

        # Update fields
        if request.email_enabled is not None:
            settings.email_enabled = request.email_enabled
        if request.telegram_enabled is not None:
            settings.telegram_enabled = request.telegram_enabled
        if request.min_interval_minutes is not None:
            settings.min_interval_minutes = request.min_interval_minutes
        if request.daily_limit is not None:
            settings.daily_limit = request.daily_limit
        if request.min_score_threshold is not None:
            settings.min_score_threshold = request.min_score_threshold
        if request.notify_top_n is not None:
            settings.notify_top_n = request.notify_top_n
        if request.notify_high_score is not None:
            settings.notify_high_score = request.notify_high_score
        if request.notify_new_signals is not None:
            settings.notify_new_signals = request.notify_new_signals
        if request.notify_position_updates is not None:
            settings.notify_position_updates = request.notify_position_updates
        if request.quiet_hours_enabled is not None:
            settings.quiet_hours_enabled = request.quiet_hours_enabled
        if request.quiet_hours_start is not None:
            settings.quiet_hours_start = request.quiet_hours_start
        if request.quiet_hours_end is not None:
            settings.quiet_hours_end = request.quiet_hours_end

        settings.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(settings)

        return {
            "success": True,
            "message": "Settings updated successfully",
            "settings": {
                "id": settings.id,
                "email_enabled": settings.email_enabled,
                "telegram_enabled": settings.telegram_enabled,
                "min_interval_minutes": settings.min_interval_minutes,
                "daily_limit": settings.daily_limit,
                "min_score_threshold": settings.min_score_threshold,
                "notify_top_n": settings.notify_top_n,
                "notify_high_score": settings.notify_high_score,
                "notify_new_signals": settings.notify_new_signals,
                "notify_position_updates": settings.notify_position_updates,
                "quiet_hours_enabled": settings.quiet_hours_enabled,
                "quiet_hours_start": settings.quiet_hours_start,
                "quiet_hours_end": settings.quiet_hours_end
            }
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/notification-settings/reset-daily-count")
async def reset_daily_notification_count(
    db: Session = Depends(get_db_session)
):
    """Reset the daily notification count"""
    try:
        from backend.database.models import NotificationSettings

        settings = db.query(NotificationSettings).first()
        if settings:
            settings.daily_count = 0
            settings.daily_count_reset_date = datetime.utcnow().strftime("%Y-%m-%d")
            db.commit()

        return {"success": True, "message": "Daily count reset"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/notification-settings/test")
async def test_notification(
    db: Session = Depends(get_db_session)
):
    """Send a test notification"""
    try:
        notification_service = NotificationService(db)

        test_results = [{
            'symbol': 'TEST/USDT',
            'total_score': 85.0,
            'current_price': 1.0,
            'btc_ratio_change_pct': 5.0,
            'eth_ratio_change_pct': 4.0,
            'volume_24h': 1000000,
            'above_sma': True,
            'macd_golden_cross': True,
            'above_all_ema': True,
            'volume_surge': False,
            'price_anomaly': False
        }]

        success = await notification_service.send_screening_alert(
            results=test_results,
            timeframe='test',
            send_email=True,
            send_telegram=True
        )

        return {
            "success": success,
            "message": "Test notification sent" if success else "Failed to send notification"
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ==================== Monitor Logs ====================

def get_docker_client():
    """Get Docker client with error handling"""
    try:
        import docker
        return docker.from_env()
    except Exception as e:
        return None


def get_container_logs(container_name: str, lines: int) -> str:
    """Get logs from a Docker container using Docker SDK"""
    client = get_docker_client()
    if not client:
        raise HTTPException(status_code=500, detail="Docker not available")

    try:
        container = client.containers.get(container_name)
        logs = container.logs(tail=lines, timestamps=False).decode('utf-8', errors='replace')
        return logs
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get logs: {str(e)}")


@router.get("/logs/monitor")
async def get_monitor_logs(
    lines: int = Query(default=200, le=2000, description="Number of lines to return"),
    search: Optional[str] = Query(default=None, description="Search keyword")
):
    """
    Get monitor service logs

    - **lines**: Number of recent lines to return (default 200, max 2000)
    - **search**: Optional search keyword to filter logs
    """
    try:
        log_lines = get_container_logs('ledger-monitor', lines)

        # Filter by search keyword
        if search:
            filtered_lines = []
            for line in log_lines.split('\n'):
                if search.lower() in line.lower():
                    filtered_lines.append(line)
            log_lines = '\n'.join(filtered_lines)

        return {
            "success": True,
            "lines": len(log_lines.split('\n')),
            "logs": log_lines
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/logs/backend")
async def get_backend_logs(
    lines: int = Query(default=200, le=2000, description="Number of lines to return")
):
    """Get backend service logs"""
    try:
        log_lines = get_container_logs('ledger-backend', lines)

        return {
            "success": True,
            "lines": len(log_lines.split('\n')),
            "logs": log_lines
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/logs/export")
async def export_logs(
    service: str = Query(default="monitor", description="Service name: monitor or backend"),
    lines: int = Query(default=500, le=5000),
    format: str = Query(default="txt", description="Export format: txt or md")
):
    """
    Export logs as downloadable file

    - **service**: monitor or backend
    - **lines**: Number of lines to export
    - **format**: txt or md
    """
    from fastapi.responses import PlainTextResponse
    from datetime import datetime

    try:
        container_name = f"ledger-{service}"
        log_content = get_container_logs(container_name, lines)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

        if format == 'md':
            # Markdown format
            content = f"""# {service.capitalize()} Service Logs

**Exported at:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**Lines:** {lines}

---

```
{log_content}
```
"""
            filename = f"{service}_logs_{timestamp}.md"
            media_type = "text/markdown"
        else:
            # Plain text format
            content = f"""=== {service.capitalize()} Service Logs ===
Exported at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Lines: {lines}
{'=' * 50}

{log_content}
"""
            filename = f"{service}_logs_{timestamp}.txt"
            media_type = "text/plain"

        return PlainTextResponse(
            content=content,
            media_type=media_type,
            headers={
                "Content-Disposition": f"attachment; filename={filename}"
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

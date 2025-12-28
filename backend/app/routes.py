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

        # Fetch data
        df = binance.fetch_ohlcv(
            symbol=request.symbol,
            timeframe=request.timeframe,
            limit=500
        )

        if df.empty:
            raise HTTPException(status_code=404, detail="No data found for symbol")

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
        df = binance.get_historical_data(
            symbol=symbol,
            timeframe=timeframe,
            days=days
        )

        if df.empty:
            raise HTTPException(status_code=404, detail="No data found")

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

        # Fetch data
        df = binance.fetch_ohlcv(symbol, timeframe, limit=500)

        if df.empty:
            raise HTTPException(status_code=404, detail="No data found")

        # Calculate indicators
        df = indicator_service.calculate_all_indicators(df)

        # Get latest values
        latest = df.iloc[-1]

        indicators = {
            'symbol': symbol,
            'timeframe': timeframe,
            'timestamp': latest['timestamp'].isoformat(),
            'price': latest['close'],
            'sma_20': latest.get('sma_20'),
            'ema_7': latest.get('ema_7'),
            'ema_14': latest.get('ema_14'),
            'ema_30': latest.get('ema_30'),
            'ema_52': latest.get('ema_52'),
            'macd': latest.get('macd'),
            'macd_signal': latest.get('macd_signal'),
            'macd_histogram': latest.get('macd_histogram'),
            'rsi': latest.get('rsi'),
            'bb_upper': latest.get('bb_upper'),
            'bb_middle': latest.get('bb_middle'),
            'bb_lower': latest.get('bb_lower'),
            'volume_sma_20': latest.get('volume_sma_20'),
            'above_sma': indicator_service.check_price_above_sma(df),
            'macd_golden_cross': indicator_service.check_macd_golden_cross(df),
            'above_all_ema': indicator_service.check_price_above_all_ema(df),
            'technical_score': indicator_service.calculate_technical_score(df),
        }

        return {
            "success": True,
            "indicators": indicators
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
        ).limit(limit).all()

        rankings = []
        for idx, row in enumerate(results, 1):
            rankings.append({
                'rank': idx,
                'symbol': row.symbol,
                'avg_score': round(row.avg_score, 2),
                'max_score': round(row.max_score, 2),
                'min_score': round(row.min_score, 2),
                'appearance_count': row.appearance_count,
                'last_seen': row.last_seen.isoformat()
            })

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

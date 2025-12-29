"""
Simulated Trading Service
模拟交易服务 - 高胜率短线策略
"""
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from backend.database.models import (
    SimAccount, SimPosition, SimTrade, AutoTradingLog,
    ScreeningResult
)
from backend.services.binance_service import BinanceService


class SimTradingService:
    """Simulated trading service with auto-trading capabilities"""

    def __init__(self, db: Session):
        self.db = db
        self.binance = BinanceService()
        self.commission_rate = 0.001  # 0.1% commission

    # ==================== Account Management ====================

    def create_account(
        self,
        account_name: str,
        initial_balance: float = 10000.0,
        **kwargs
    ) -> SimAccount:
        """Create a new simulated trading account"""
        account = SimAccount(
            account_name=account_name,
            initial_balance=initial_balance,
            current_balance=initial_balance,
            frozen_balance=0.0,
            total_equity=initial_balance,
            **kwargs
        )
        self.db.add(account)
        self.db.commit()
        self.db.refresh(account)
        return account

    def get_account(self, account_id: int) -> Optional[SimAccount]:
        """Get account by ID"""
        return self.db.query(SimAccount).filter(
            SimAccount.id == account_id
        ).first()

    def get_all_accounts(self) -> List[SimAccount]:
        """Get all active accounts"""
        return self.db.query(SimAccount).filter(
            SimAccount.is_active == True
        ).all()

    def update_account_equity(self, account_id: int):
        """Update account equity based on current positions"""
        account = self.get_account(account_id)
        if not account:
            return

        # Get all open positions
        positions = self.get_open_positions(account_id)

        # Calculate total position value at current prices
        total_position_value = 0.0
        frozen_balance = 0.0

        for position in positions:
            # Update position current price
            current_price = self._get_current_price(position.symbol)
            if current_price:
                position.current_price = current_price
                position.current_value = position.remaining_quantity * current_price
                position.unrealized_pnl = position.current_value - (
                    position.remaining_quantity * position.entry_price
                )
                position.unrealized_pnl_pct = (
                    position.unrealized_pnl / (position.remaining_quantity * position.entry_price)
                ) * 100 if position.entry_price > 0 else 0

                total_position_value += position.current_value
                frozen_balance += position.remaining_quantity * position.entry_price

        # Update account
        account.frozen_balance = frozen_balance
        account.total_equity = account.current_balance + total_position_value
        account.updated_at = datetime.utcnow()

        self.db.commit()

    # ==================== Position Management ====================

    def open_position(
        self,
        account_id: int,
        symbol: str,
        entry_price: float,
        position_size_pct: float = None,
        entry_score: float = None,
        entry_signals: Dict = None
    ) -> Tuple[bool, str, Optional[SimPosition]]:
        """
        Open a new position

        Returns:
            (success, message, position)
        """
        account = self.get_account(account_id)
        if not account:
            return False, "Account not found", None

        # Check if already have position for this symbol
        existing = self.db.query(SimPosition).filter(
            and_(
                SimPosition.account_id == account_id,
                SimPosition.symbol == symbol,
                SimPosition.is_closed == False
            )
        ).first()

        if existing:
            return False, f"Already have open position for {symbol}", None

        # Check max positions
        open_positions_count = self.db.query(SimPosition).filter(
            and_(
                SimPosition.account_id == account_id,
                SimPosition.is_closed == False
            )
        ).count()

        if open_positions_count >= account.max_positions:
            return False, f"Max positions reached ({account.max_positions})", None

        # Calculate position size
        if position_size_pct is None:
            position_size_pct = account.position_size_pct

        position_value = account.total_equity * (position_size_pct / 100.0)

        # Check if sufficient balance
        if position_value > account.current_balance:
            return False, "Insufficient balance", None

        # Calculate quantity
        quantity = position_value / entry_price

        # Calculate commission
        commission = position_value * self.commission_rate

        # Calculate stop loss and take profit prices
        stop_loss_price = entry_price * (1 - account.stop_loss_pct / 100.0)

        take_profit_prices = [
            entry_price * (1 + tp_pct / 100.0)
            for tp_pct in account.take_profit_levels
        ]

        # Create position
        position = SimPosition(
            account_id=account_id,
            symbol=symbol,
            entry_price=entry_price,
            entry_time=datetime.utcnow(),
            quantity=quantity,
            entry_value=position_value,
            entry_score=entry_score,
            current_price=entry_price,
            current_value=position_value,
            stop_loss_price=stop_loss_price,
            take_profit_prices=take_profit_prices,
            remaining_quantity=quantity,
            entry_signals=entry_signals or {}
        )
        self.db.add(position)

        # Create trade record
        trade = SimTrade(
            account_id=account_id,
            symbol=symbol,
            side='BUY',
            price=entry_price,
            quantity=quantity,
            value=position_value,
            commission=commission,
            trade_type='ENTRY',
            entry_score=entry_score,
            signals=entry_signals or {},
            trade_time=datetime.utcnow()
        )
        self.db.add(trade)

        # Update account balance
        account.current_balance -= (position_value + commission)
        account.total_trades += 1
        account.total_commission += commission

        self.db.commit()
        self.db.refresh(position)

        # Link trade to position
        trade.position_id = position.id
        self.db.commit()

        return True, f"Position opened: {symbol} @ {entry_price}", position

    def close_position(
        self,
        position_id: int,
        close_price: float = None,
        close_reason: str = 'MANUAL',
        partial_pct: float = 100.0
    ) -> Tuple[bool, str]:
        """
        Close a position (full or partial)

        Args:
            position_id: Position ID
            close_price: Close price (if None, use current market price)
            close_reason: Reason for closing
            partial_pct: Percentage to close (100 = full close)

        Returns:
            (success, message)
        """
        position = self.db.query(SimPosition).filter(
            SimPosition.id == position_id
        ).first()

        if not position or position.is_closed:
            return False, "Position not found or already closed"

        account = self.get_account(position.account_id)
        if not account:
            return False, "Account not found"

        # Get current price if not provided
        if close_price is None:
            close_price = self._get_current_price(position.symbol)
            if not close_price:
                return False, "Failed to get current price"

        # Calculate quantity to close
        close_quantity = position.remaining_quantity * (partial_pct / 100.0)
        close_value = close_quantity * close_price

        # Calculate P&L
        entry_value = close_quantity * position.entry_price
        pnl = close_value - entry_value
        pnl_pct = (pnl / entry_value) * 100 if entry_value > 0 else 0

        # Calculate commission
        commission = close_value * self.commission_rate

        # Create trade record
        trade_type = 'FULL_EXIT' if partial_pct >= 99.9 else 'PARTIAL_EXIT'
        trade = SimTrade(
            account_id=position.account_id,
            position_id=position.id,
            symbol=position.symbol,
            side='SELL',
            price=close_price,
            quantity=close_quantity,
            value=close_value,
            commission=commission,
            pnl=pnl,
            pnl_pct=pnl_pct,
            trade_type=trade_type,
            exit_reason=close_reason,
            entry_score=position.entry_score,
            signals=position.entry_signals,
            trade_time=datetime.utcnow()
        )
        self.db.add(trade)

        # Update position
        position.remaining_quantity -= close_quantity

        # Record partial exit
        if not position.partial_exits:
            position.partial_exits = []
        position.partial_exits.append({
            'price': close_price,
            'quantity': close_quantity,
            'time': datetime.utcnow().isoformat(),
            'reason': close_reason,
            'pnl': pnl,
            'pnl_pct': pnl_pct
        })

        # If full close
        if position.remaining_quantity < 0.0001:  # Essentially zero
            position.is_closed = True
            position.close_time = datetime.utcnow()
            position.close_reason = close_reason

        # Update account
        account.current_balance += (close_value - commission)
        account.total_pnl += pnl
        account.total_commission += commission

        if pnl > 0:
            account.winning_trades += 1
        else:
            account.losing_trades += 1

        self.db.commit()

        return True, f"Position closed: {position.symbol} @ {close_price}, P&L: {pnl:.2f} ({pnl_pct:.2f}%)"

    def check_and_execute_exits(self, account_id: int) -> List[Dict]:
        """
        Check all open positions for stop loss / take profit
        Returns list of executed exits
        """
        positions = self.get_open_positions(account_id)
        exits = []

        for position in positions:
            # Get current price
            current_price = self._get_current_price(position.symbol)
            if not current_price:
                continue

            # Update position current price
            position.current_price = current_price
            position.current_value = position.remaining_quantity * current_price
            position.unrealized_pnl = position.current_value - (
                position.remaining_quantity * position.entry_price
            )
            position.unrealized_pnl_pct = (
                position.unrealized_pnl / (position.remaining_quantity * position.entry_price)
            ) * 100 if position.entry_price > 0 else 0

            # Check stop loss
            if current_price <= position.stop_loss_price:
                success, msg = self.close_position(
                    position.id,
                    close_price=current_price,
                    close_reason='STOP_LOSS',
                    partial_pct=100.0
                )
                if success:
                    exits.append({
                        'symbol': position.symbol,
                        'type': 'STOP_LOSS',
                        'price': current_price,
                        'message': msg
                    })
                continue

            # Check take profit levels
            tp_prices = position.take_profit_prices or []
            for i, tp_price in enumerate(tp_prices):
                if current_price >= tp_price:
                    # Partial exit (33% each for 3 levels)
                    partial_pct = 100.0 / len(tp_prices)

                    success, msg = self.close_position(
                        position.id,
                        close_price=current_price,
                        close_reason=f'TAKE_PROFIT_{i+1}',
                        partial_pct=partial_pct
                    )

                    if success:
                        exits.append({
                            'symbol': position.symbol,
                            'type': f'TAKE_PROFIT_{i+1}',
                            'price': current_price,
                            'partial_pct': partial_pct,
                            'message': msg
                        })

                        # Remove this TP level so we don't trigger it again
                        position.take_profit_prices = [
                            p for j, p in enumerate(tp_prices) if j != i
                        ]
                        self.db.commit()
                        break

        self.db.commit()
        return exits

    def get_open_positions(self, account_id: int) -> List[SimPosition]:
        """Get all open positions for an account"""
        return self.db.query(SimPosition).filter(
            and_(
                SimPosition.account_id == account_id,
                SimPosition.is_closed == False
            )
        ).order_by(SimPosition.entry_time.desc()).all()

    def get_position_history(
        self,
        account_id: int,
        limit: int = 50
    ) -> List[SimPosition]:
        """Get closed positions history"""
        return self.db.query(SimPosition).filter(
            and_(
                SimPosition.account_id == account_id,
                SimPosition.is_closed == True
            )
        ).order_by(SimPosition.close_time.desc()).limit(limit).all()

    # ==================== Auto Trading Logic ====================

    def evaluate_screening_result(
        self,
        account: SimAccount,
        screening_result: Dict
    ) -> Tuple[bool, str]:
        """
        Evaluate if a screening result meets entry criteria

        Returns:
            (should_enter, reason)
        """
        # Check total score
        if screening_result['total_score'] < account.entry_score_min:
            return False, f"Total score too low: {screening_result['total_score']:.1f} < {account.entry_score_min}"

        # Check technical score
        if screening_result['technical_score'] < account.entry_technical_min:
            return False, f"Technical score too low: {screening_result['technical_score']:.1f} < {account.entry_technical_min}"

        # Check required signals
        required_signals = {
            'macd_golden_cross': screening_result.get('macd_golden_cross', False),
            'above_all_ema': screening_result.get('above_all_ema', False),
        }

        if not required_signals['macd_golden_cross']:
            return False, "Missing MACD golden cross signal"

        if not required_signals['above_all_ema']:
            return False, "Missing price above all EMA signal"

        # Check RSI (avoid overbought)
        # We don't have RSI in screening_result, but it's already factored into technical_score

        # Check volume
        if screening_result.get('volume_score', 0) < 40:
            return False, f"Volume too low: {screening_result.get('volume_score', 0)}"

        return True, "All entry criteria met"

    def auto_trade_monitor(self, account_id: int) -> Dict:
        """
        Monitor screening results and auto-open positions

        Returns:
            Summary of actions taken
        """
        account = self.get_account(account_id)
        if not account or not account.auto_trading_enabled:
            return {'error': 'Account not found or auto-trading disabled'}

        # Get latest screening results (within last 10 minutes)
        time_threshold = datetime.utcnow() - timedelta(minutes=10)
        screening_results = self.db.query(ScreeningResult).filter(
            ScreeningResult.timestamp >= time_threshold
        ).order_by(
            ScreeningResult.total_score.desc()
        ).limit(20).all()

        actions = {
            'positions_opened': [],
            'positions_skipped': [],
            'positions_closed': []
        }

        # First, check and execute exits on existing positions
        exits = self.check_and_execute_exits(account_id)
        actions['positions_closed'] = exits

        # Update account equity
        self.update_account_equity(account_id)

        # Check if we can open new positions
        open_positions_count = len(self.get_open_positions(account_id))

        if open_positions_count >= account.max_positions:
            self._log_auto_trading(
                account_id,
                action='SKIP',
                symbol=None,
                reason=f'Max positions reached ({account.max_positions})',
                success=True
            )
            return actions

        # Evaluate screening results
        for result in screening_results:
            # Convert to dict
            result_dict = {
                'symbol': result.symbol,
                'total_score': result.total_score,
                'technical_score': result.technical_score,
                'beta_score': result.beta_score,
                'volume_score': result.volume_score,
                'macd_golden_cross': result.macd_golden_cross,
                'above_all_ema': result.above_all_ema,
                'above_sma': result.above_sma,
                'volume_surge': result.volume_surge,
                'current_price': result.current_price,
            }

            # Evaluate entry criteria
            should_enter, reason = self.evaluate_screening_result(account, result_dict)

            if not should_enter:
                actions['positions_skipped'].append({
                    'symbol': result.symbol,
                    'score': result.total_score,
                    'reason': reason
                })
                self._log_auto_trading(
                    account_id,
                    action='SKIP',
                    symbol=result.symbol,
                    reason=reason,
                    screening_score=result.total_score,
                    screening_data=result_dict,
                    success=True
                )
                continue

            # Try to open position
            success, msg, position = self.open_position(
                account_id=account_id,
                symbol=result.symbol,
                entry_price=result.current_price,
                entry_score=result.total_score,
                entry_signals=result_dict
            )

            if success:
                actions['positions_opened'].append({
                    'symbol': result.symbol,
                    'price': result.current_price,
                    'score': result.total_score,
                    'message': msg
                })
                self._log_auto_trading(
                    account_id,
                    action='OPEN_POSITION',
                    symbol=result.symbol,
                    reason='Entry criteria met',
                    screening_score=result.total_score,
                    screening_data=result_dict,
                    success=True
                )

                # Check if reached max positions
                open_positions_count += 1
                if open_positions_count >= account.max_positions:
                    break
            else:
                actions['positions_skipped'].append({
                    'symbol': result.symbol,
                    'score': result.total_score,
                    'reason': msg
                })
                self._log_auto_trading(
                    account_id,
                    action='OPEN_POSITION',
                    symbol=result.symbol,
                    reason=msg,
                    screening_score=result.total_score,
                    screening_data=result_dict,
                    success=False,
                    error_message=msg
                )

        return actions

    def _log_auto_trading(
        self,
        account_id: int,
        action: str,
        symbol: Optional[str],
        reason: str,
        screening_score: float = None,
        screening_data: Dict = None,
        success: bool = False,
        error_message: str = None
    ):
        """Log auto trading decision"""
        log = AutoTradingLog(
            account_id=account_id,
            action=action,
            symbol=symbol,
            reason=reason,
            screening_score=screening_score,
            screening_data=screening_data,
            success=success,
            error_message=error_message
        )
        self.db.add(log)
        self.db.commit()

    # ==================== Helper Methods ====================

    def _get_current_price(self, symbol: str) -> Optional[float]:
        """Get current market price for a symbol"""
        try:
            ticker = self.binance.fetch_ticker(symbol)
            return ticker.get('last', None) if ticker else None
        except Exception as e:
            print(f"Error fetching price for {symbol}: {e}")
            return None

    def get_account_summary(self, account_id: int) -> Dict:
        """Get comprehensive account summary"""
        account = self.get_account(account_id)
        if not account:
            return {}

        # Update equity first
        self.update_account_equity(account_id)
        self.db.refresh(account)

        # Get positions
        open_positions = self.get_open_positions(account_id)

        # Get recent trades
        recent_trades = self.db.query(SimTrade).filter(
            SimTrade.account_id == account_id
        ).order_by(SimTrade.trade_time.desc()).limit(20).all()

        # Calculate win rate
        total = account.winning_trades + account.losing_trades
        win_rate = (account.winning_trades / total * 100) if total > 0 else 0

        # Calculate total return
        total_return = account.total_equity - account.initial_balance
        total_return_pct = (total_return / account.initial_balance * 100) if account.initial_balance > 0 else 0

        return {
            'account_id': account.id,
            'account_name': account.account_name,
            'initial_balance': account.initial_balance,
            'current_balance': account.current_balance,
            'frozen_balance': account.frozen_balance,
            'total_equity': account.total_equity,
            'total_return': total_return,
            'total_return_pct': total_return_pct,
            'total_pnl': account.total_pnl,
            'total_trades': account.total_trades,
            'winning_trades': account.winning_trades,
            'losing_trades': account.losing_trades,
            'win_rate': win_rate,
            'total_commission': account.total_commission,
            'auto_trading_enabled': account.auto_trading_enabled,
            'max_positions': account.max_positions,
            'open_positions_count': len(open_positions),
            'open_positions': [self._position_to_dict(p) for p in open_positions],
            'recent_trades': [self._trade_to_dict(t) for t in recent_trades],
        }

    @staticmethod
    def _position_to_dict(position: SimPosition) -> Dict:
        """Convert position to dict"""
        return {
            'id': position.id,
            'symbol': position.symbol,
            'entry_price': position.entry_price,
            'entry_time': position.entry_time.isoformat(),
            'quantity': position.quantity,
            'remaining_quantity': position.remaining_quantity,
            'entry_value': position.entry_value,
            'entry_score': position.entry_score,
            'current_price': position.current_price,
            'current_value': position.current_value,
            'unrealized_pnl': position.unrealized_pnl,
            'unrealized_pnl_pct': position.unrealized_pnl_pct,
            'stop_loss_price': position.stop_loss_price,
            'take_profit_prices': position.take_profit_prices,
            'is_closed': position.is_closed,
            'partial_exits': position.partial_exits or [],
        }

    @staticmethod
    def _trade_to_dict(trade: SimTrade) -> Dict:
        """Convert trade to dict"""
        return {
            'id': trade.id,
            'symbol': trade.symbol,
            'side': trade.side,
            'price': trade.price,
            'quantity': trade.quantity,
            'value': trade.value,
            'commission': trade.commission,
            'pnl': trade.pnl,
            'pnl_pct': trade.pnl_pct,
            'trade_type': trade.trade_type,
            'exit_reason': trade.exit_reason,
            'entry_score': trade.entry_score,
            'trade_time': trade.trade_time.isoformat(),
        }

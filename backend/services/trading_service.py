from typing import Dict, List, Optional
from datetime import datetime
from sqlalchemy.orm import Session

from backend.services.binance_service import BinanceService
from backend.database.models import Order, Watchlist
from backend.config import settings


class TradingService:
    """Service for executing trades on Binance"""

    def __init__(self, db: Session):
        self.db = db
        self.binance = BinanceService()

    def create_market_order(
        self,
        symbol: str,
        side: str,  # 'BUY' or 'SELL'
        quantity: float,
        notes: str = None
    ) -> Dict:
        """
        Create a market order

        Args:
            symbol: Trading pair (e.g., 'BTC/USDT')
            side: 'BUY' or 'SELL'
            quantity: Amount to buy/sell
            notes: Optional notes

        Returns:
            Order details
        """
        try:
            # Validate inputs
            if side not in ['BUY', 'SELL']:
                raise ValueError("Side must be 'BUY' or 'SELL'")

            if quantity <= 0:
                raise ValueError("Quantity must be positive")

            # Create order in database first
            order = Order(
                symbol=symbol,
                side=side,
                order_type='MARKET',
                quantity=quantity,
                status='PENDING',
                notes=notes
            )
            self.db.add(order)
            self.db.commit()
            self.db.refresh(order)

            # Execute order on Binance
            try:
                result = self.binance.exchange.create_market_order(
                    symbol=symbol,
                    side=side.lower(),
                    amount=quantity
                )

                # Update order with execution details
                order.exchange_order_id = result.get('id')
                order.status = 'FILLED' if result.get('status') == 'closed' else 'PENDING'
                order.filled_quantity = result.get('filled', 0)
                order.avg_fill_price = result.get('average')
                order.executed_at = datetime.utcnow()

                # Get fee info
                if 'fee' in result:
                    order.commission = result['fee'].get('cost')
                    order.commission_asset = result['fee'].get('currency')

                self.db.commit()
                self.db.refresh(order)

                return self._order_to_dict(order)

            except Exception as e:
                # Mark order as failed
                order.status = 'FAILED'
                order.notes = f"{order.notes or ''}\nError: {str(e)}"
                self.db.commit()
                raise

        except Exception as e:
            self.db.rollback()
            raise Exception(f"Failed to create market order: {str(e)}")

    def create_limit_order(
        self,
        symbol: str,
        side: str,
        quantity: float,
        price: float,
        notes: str = None
    ) -> Dict:
        """
        Create a limit order

        Args:
            symbol: Trading pair
            side: 'BUY' or 'SELL'
            quantity: Amount to buy/sell
            price: Limit price
            notes: Optional notes

        Returns:
            Order details
        """
        try:
            # Validate inputs
            if side not in ['BUY', 'SELL']:
                raise ValueError("Side must be 'BUY' or 'SELL'")

            if quantity <= 0 or price <= 0:
                raise ValueError("Quantity and price must be positive")

            # Create order in database
            order = Order(
                symbol=symbol,
                side=side,
                order_type='LIMIT',
                quantity=quantity,
                price=price,
                status='PENDING',
                notes=notes
            )
            self.db.add(order)
            self.db.commit()
            self.db.refresh(order)

            # Execute order on Binance
            try:
                result = self.binance.exchange.create_limit_order(
                    symbol=symbol,
                    side=side.lower(),
                    amount=quantity,
                    price=price
                )

                # Update order
                order.exchange_order_id = result.get('id')
                order.status = result.get('status', 'PENDING').upper()
                order.filled_quantity = result.get('filled', 0)
                order.avg_fill_price = result.get('average')

                if result.get('status') in ['closed', 'filled']:
                    order.executed_at = datetime.utcnow()

                if 'fee' in result:
                    order.commission = result['fee'].get('cost')
                    order.commission_asset = result['fee'].get('currency')

                self.db.commit()
                self.db.refresh(order)

                return self._order_to_dict(order)

            except Exception as e:
                order.status = 'FAILED'
                order.notes = f"{order.notes or ''}\nError: {str(e)}"
                self.db.commit()
                raise

        except Exception as e:
            self.db.rollback()
            raise Exception(f"Failed to create limit order: {str(e)}")

    def cancel_order(self, order_id: int) -> Dict:
        """Cancel an open order"""
        try:
            order = self.db.query(Order).filter(Order.id == order_id).first()
            if not order:
                raise ValueError(f"Order {order_id} not found")

            if order.status not in ['PENDING', 'OPEN']:
                raise ValueError(f"Cannot cancel order with status {order.status}")

            # Cancel on Binance
            if order.exchange_order_id:
                self.binance.exchange.cancel_order(
                    id=order.exchange_order_id,
                    symbol=order.symbol
                )

            # Update order status
            order.status = 'CANCELLED'
            order.updated_at = datetime.utcnow()
            self.db.commit()
            self.db.refresh(order)

            return self._order_to_dict(order)

        except Exception as e:
            self.db.rollback()
            raise Exception(f"Failed to cancel order: {str(e)}")

    def get_order_history(
        self,
        symbol: str = None,
        limit: int = 50
    ) -> List[Dict]:
        """Get order history"""
        try:
            query = self.db.query(Order)

            if symbol:
                query = query.filter(Order.symbol == symbol)

            orders = query.order_by(Order.created_at.desc()).limit(limit).all()

            return [self._order_to_dict(order) for order in orders]

        except Exception as e:
            print(f"Error getting order history: {e}")
            return []

    def get_balance(self, asset: str = 'USDT') -> Dict:
        """Get account balance for an asset"""
        try:
            balance = self.binance.exchange.fetch_balance()
            return {
                'asset': asset,
                'free': balance.get('free', {}).get(asset, 0),
                'used': balance.get('used', {}).get(asset, 0),
                'total': balance.get('total', {}).get(asset, 0)
            }
        except Exception as e:
            raise Exception(f"Failed to get balance: {str(e)}")

    def get_all_balances(self) -> List[Dict]:
        """Get all non-zero balances"""
        try:
            balance = self.binance.exchange.fetch_balance()
            balances = []

            for asset, amount in balance.get('total', {}).items():
                if amount > 0:
                    balances.append({
                        'asset': asset,
                        'free': balance['free'].get(asset, 0),
                        'used': balance['used'].get(asset, 0),
                        'total': amount
                    })

            return sorted(balances, key=lambda x: x['total'], reverse=True)

        except Exception as e:
            raise Exception(f"Failed to get balances: {str(e)}")

    # Watchlist methods
    def add_to_watchlist(self, symbol: str, notes: str = None) -> Dict:
        """Add symbol to watchlist"""
        try:
            # Check if already exists
            existing = self.db.query(Watchlist).filter(
                Watchlist.symbol == symbol
            ).first()

            if existing:
                return {'success': False, 'message': 'Symbol already in watchlist'}

            watchlist_item = Watchlist(symbol=symbol, notes=notes)
            self.db.add(watchlist_item)
            self.db.commit()
            self.db.refresh(watchlist_item)

            return {
                'success': True,
                'symbol': watchlist_item.symbol,
                'added_at': watchlist_item.added_at.isoformat()
            }

        except Exception as e:
            self.db.rollback()
            raise Exception(f"Failed to add to watchlist: {str(e)}")

    def remove_from_watchlist(self, symbol: str) -> Dict:
        """Remove symbol from watchlist"""
        try:
            watchlist_item = self.db.query(Watchlist).filter(
                Watchlist.symbol == symbol
            ).first()

            if not watchlist_item:
                return {'success': False, 'message': 'Symbol not in watchlist'}

            self.db.delete(watchlist_item)
            self.db.commit()

            return {'success': True, 'message': f'{symbol} removed from watchlist'}

        except Exception as e:
            self.db.rollback()
            raise Exception(f"Failed to remove from watchlist: {str(e)}")

    def get_watchlist(self) -> List[Dict]:
        """Get all watchlist symbols"""
        try:
            items = self.db.query(Watchlist).order_by(Watchlist.added_at.desc()).all()
            return [{
                'symbol': item.symbol,
                'notes': item.notes,
                'added_at': item.added_at.isoformat()
            } for item in items]

        except Exception as e:
            print(f"Error getting watchlist: {e}")
            return []

    def _order_to_dict(self, order: Order) -> Dict:
        """Convert Order model to dictionary"""
        return {
            'id': order.id,
            'symbol': order.symbol,
            'side': order.side,
            'order_type': order.order_type,
            'quantity': order.quantity,
            'price': order.price,
            'stop_price': order.stop_price,
            'status': order.status,
            'exchange_order_id': order.exchange_order_id,
            'filled_quantity': order.filled_quantity,
            'avg_fill_price': order.avg_fill_price,
            'commission': order.commission,
            'commission_asset': order.commission_asset,
            'created_at': order.created_at.isoformat() if order.created_at else None,
            'executed_at': order.executed_at.isoformat() if order.executed_at else None,
            'notes': order.notes
        }

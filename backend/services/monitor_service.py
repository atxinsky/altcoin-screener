import asyncio
import schedule
import time
from datetime import datetime
from typing import Dict, List, Optional
from sqlalchemy.orm import Session
import pytz

from backend.database.database import get_db
from backend.database.models import NotificationSettings
from backend.services.screening_service import ScreeningService
from backend.services.notification_service import NotificationService
from backend.services.sim_trading_service import SimTradingService
from backend.config import settings
# K-line collector now runs as continuous background thread in backend
from datetime import timedelta


class MonitorService:
    """Service for continuous monitoring and alerts"""

    def __init__(self):
        self.is_running = False
        self.screening_interval = settings.UPDATE_INTERVAL  # seconds
        self.beijing_tz = pytz.timezone('Asia/Shanghai')

        # 优选交易时间段（北京时间）- 这些时段会获得额外权重加成，但不强制限制
        # 格式: [(开始小时, 开始分钟, 结束小时, 结束分钟), ...]
        self.trading_windows = [
            (7, 30, 8, 30),    # 7:30-8:30
            (11, 30, 12, 30),  # 11:30-12:30
            (15, 30, 16, 30),  # 15:30-16:30
        ]
        self.trading_window_bonus = 5.0  # 优选时段额外加分

    def is_in_trading_window(self) -> bool:
        """检查当前北京时间是否在优选交易时间窗口内（用于加分，不是限制）"""
        now = datetime.now(self.beijing_tz)
        current_minutes = now.hour * 60 + now.minute

        for start_hour, start_min, end_hour, end_min in self.trading_windows:
            start_minutes = start_hour * 60 + start_min
            end_minutes = end_hour * 60 + end_min

            if start_minutes <= current_minutes <= end_minutes:
                return True

        return False

    def get_time_window_bonus(self) -> float:
        """获取当前时间窗口的加分值"""
        if self.is_in_trading_window():
            return self.trading_window_bonus
        return 0.0

    def get_next_trading_window(self) -> Optional[str]:
        """获取下一个交易时间窗口"""
        now = datetime.now(self.beijing_tz)
        current_minutes = now.hour * 60 + now.minute

        for start_hour, start_min, end_hour, end_min in self.trading_windows:
            start_minutes = start_hour * 60 + start_min

            if current_minutes < start_minutes:
                return f"{start_hour:02d}:{start_min:02d}"

        # 如果当天所有窗口都过了，返回明天第一个窗口
        start_hour, start_min, _, _ = self.trading_windows[0]
        return f"明天 {start_hour:02d}:{start_min:02d}"

    def _get_notification_settings(self, db: Session) -> NotificationSettings:
        """获取通知设置，如果不存在则创建默认设置"""
        ns = db.query(NotificationSettings).first()
        if not ns:
            ns = NotificationSettings()
            db.add(ns)
            db.commit()
            db.refresh(ns)
        return ns

    def _can_send_notification(self, db: Session, ns: NotificationSettings) -> tuple:
        """
        检查是否可以发送通知

        Returns:
            (can_send, reason)
        """
        beijing_now = datetime.now(self.beijing_tz)
        current_hour = beijing_now.hour

        # 检查静默时段
        if ns.quiet_hours_enabled:
            if ns.quiet_hours_start > ns.quiet_hours_end:
                # 跨午夜的静默时段，如 22:00 - 07:00
                if current_hour >= ns.quiet_hours_start or current_hour < ns.quiet_hours_end:
                    return False, f"静默时段 ({ns.quiet_hours_start}:00-{ns.quiet_hours_end}:00)"
            else:
                # 非跨午夜，如 13:00 - 14:00
                if ns.quiet_hours_start <= current_hour < ns.quiet_hours_end:
                    return False, f"静默时段 ({ns.quiet_hours_start}:00-{ns.quiet_hours_end}:00)"

        # 检查每日限制
        today_str = beijing_now.strftime("%Y-%m-%d")
        if ns.daily_count_reset_date != today_str:
            # 新的一天，重置计数
            ns.daily_count = 0
            ns.daily_count_reset_date = today_str
            db.commit()

        if ns.daily_count >= ns.daily_limit:
            return False, f"达到每日限制 ({ns.daily_limit}次)"

        # 检查最小间隔
        if ns.last_notification_time:
            time_since_last = datetime.utcnow() - ns.last_notification_time
            min_interval = timedelta(minutes=ns.min_interval_minutes)
            if time_since_last < min_interval:
                remaining = min_interval - time_since_last
                return False, f"距上次通知不足 {ns.min_interval_minutes} 分钟 (还需 {int(remaining.total_seconds() / 60)} 分钟)"

        return True, "可以发送"

    def _update_notification_stats(self, db: Session, ns: NotificationSettings):
        """更新通知统计"""
        ns.last_notification_time = datetime.utcnow()
        ns.daily_count += 1
        db.commit()

    async def run_screening_job(self, timeframes: List[str] = None):
        """Run screening job for specified timeframes"""
        if timeframes is None:
            timeframes = ['5m', '15m', '1h']

        beijing_now = datetime.now(self.beijing_tz)
        in_window = self.is_in_trading_window()

        time_bonus = self.get_time_window_bonus()
        print(f"[{beijing_now.strftime('%Y-%m-%d %H:%M:%S')} 北京时间] Running screening job...")
        if in_window:
            print(f"  ★ 当前在优选时段内，额外加分: +{time_bonus}")
        else:
            next_window = self.get_next_trading_window()
            print(f"  ○ 普通时段（下一优选时段: {next_window}）")

        with get_db() as db:
            screening_service = ScreeningService(db)
            notification_service = NotificationService(db)
            sim_trading_service = SimTradingService(db)

            # 获取通知设置
            ns = self._get_notification_settings(db)

            all_results = []

            for timeframe in timeframes:
                try:
                    print(f"  Screening {timeframe} timeframe...")
                    results = screening_service.screen_altcoins(
                        timeframe=timeframe,
                        min_volume=settings.MIN_VOLUME_USD
                    )

                    # 使用通知设置中的分数阈值过滤
                    high_score_results = [
                        r for r in results
                        if r['total_score'] >= ns.min_score_threshold
                    ]

                    if high_score_results:
                        all_results.extend(high_score_results)
                        print(f"  Found {len(high_score_results)} high-score opportunities in {timeframe}")

                except Exception as e:
                    print(f"  Error screening {timeframe}: {e}")

            # Send notification if high-score opportunities found
            if all_results and ns.notify_high_score:
                # 检查是否可以发送通知
                can_send, reason = self._can_send_notification(db, ns)

                if can_send and (ns.email_enabled or ns.telegram_enabled):
                    try:
                        # 按分数排序并取前N个
                        all_results.sort(key=lambda x: x['total_score'], reverse=True)
                        results_to_notify = all_results[:ns.notify_top_n]

                        await notification_service.send_screening_alert(
                            results=results_to_notify,
                            timeframe='multi',
                            send_email=ns.email_enabled,
                            send_telegram=ns.telegram_enabled
                        )

                        # 更新通知统计
                        self._update_notification_stats(db, ns)

                        print(f"  ✓ 通知已发送: {len(results_to_notify)} 个机会 (今日第 {ns.daily_count} 次)")
                    except Exception as e:
                        print(f"  ✗ 发送通知失败: {e}")
                else:
                    print(f"  ✗ 跳过通知: {reason}")

            # 自动模拟交易 - 全天候执行，不再限制时间窗口
            try:
                accounts = sim_trading_service.get_all_accounts()
                for account in accounts:
                    if account.auto_trading_enabled:
                        print(f"  Auto trading check: {account.account_name}")
                        actions = sim_trading_service.auto_trade_monitor(
                            account.id,
                            time_window_bonus=time_bonus
                        )

                        if actions.get('positions_opened'):
                            print(f"    Opened {len(actions['positions_opened'])} positions")
                            for pos in actions['positions_opened']:
                                bonus_str = f" [+{time_bonus}bonus]" if time_bonus > 0 else ""
                                print(f"      - {pos['symbol']} @ {pos['price']:.6f} (score: {pos['score']:.1f}{bonus_str})")

                        if actions.get('positions_closed'):
                            print(f"    Closed {len(actions['positions_closed'])} positions")

            except Exception as e:
                print(f"  Auto trading error: {e}")
                import traceback
                traceback.print_exc()

        print(f"[{datetime.now(self.beijing_tz).strftime('%H:%M:%S')}] Screening job completed\n")

    def start_monitoring(self, timeframes: List[str] = None,
                         trading_windows: List[tuple] = None):
        """
        Start continuous monitoring

        Args:
            timeframes: List of timeframes to screen
            trading_windows: List of preferred trading windows [(start_h, start_m, end_h, end_m), ...]
        """
        self.is_running = True

        if trading_windows is not None:
            self.trading_windows = trading_windows

        print(f"Starting monitoring service (interval: {self.screening_interval}s)...")
        print("Trading mode: 24/7 (no time restriction)")
        print(f"Preferred windows with +{self.trading_window_bonus} bonus (Beijing time):")
        for start_h, start_m, end_h, end_m in self.trading_windows:
            print(f"  - {start_h:02d}:{start_m:02d} - {end_h:02d}:{end_m:02d}")

        # Schedule periodic screening
        schedule.every(self.screening_interval).seconds.do(
            lambda: asyncio.run(self.run_screening_job(timeframes))
        )

        # Schedule data cleanup every 10 days
        schedule.every(10).days.do(self._run_cleanup)
        print("Data cleanup scheduled: every 10 days")

        # Run initial screening immediately
        asyncio.run(self.run_screening_job(timeframes))

        # Keep running
        while self.is_running:
            schedule.run_pending()
            time.sleep(1)

    def _run_cleanup(self):
        """Run data cleanup task"""
        try:
            from backend.database.session import get_db_session
            from backend.services.screening_service import ScreeningService

            db = next(get_db_session())
            screening_service = ScreeningService(db)
            deleted = screening_service.cleanup_old_data(
                kline_days_short=15,  # Keep 5m/15m klines for 15 days
                kline_days_long=90,   # Keep 1h/4h/1d klines for 90 days
                screening_days=7      # Keep screening results for 7 days
            )
            db.close()

            total = sum(deleted.values())
            if total > 0:
                print(f"[Scheduled Cleanup] Cleaned {total} old records")
        except Exception as e:
            print(f"[Scheduled Cleanup] Error: {e}")

    def stop_monitoring(self):
        """Stop monitoring"""
        self.is_running = False
        print("Monitoring service stopped")


# Standalone monitoring script
if __name__ == "__main__":
    monitor = MonitorService()

    print("""
    ============================================================
         Binance Altcoin Screener - Monitor Service

      24/7 Trading Mode - No time window restrictions
      Preferred windows get +5 bonus points

      Press Ctrl+C to stop
    ============================================================
    """)

    try:
        monitor.start_monitoring(timeframes=['5m', '15m', '1h'])
    except KeyboardInterrupt:
        print("\n\nShutting down gracefully...")
        monitor.stop_monitoring()

import asyncio
import schedule
import time
from datetime import datetime
from typing import Dict, List
from sqlalchemy.orm import Session

from backend.database.database import get_db
from backend.services.screening_service import ScreeningService
from backend.services.notification_service import NotificationService
from backend.config import settings


class MonitorService:
    """Service for continuous monitoring and alerts"""

    def __init__(self):
        self.is_running = False
        self.screening_interval = settings.UPDATE_INTERVAL  # seconds

    async def run_screening_job(self, timeframes: List[str] = None):
        """Run screening job for specified timeframes"""
        if timeframes is None:
            timeframes = ['5m', '15m', '1h']

        print(f"[{datetime.now()}] Running screening job...")

        with get_db() as db:
            screening_service = ScreeningService(db)
            notification_service = NotificationService(db)

            all_results = []

            for timeframe in timeframes:
                try:
                    print(f"  Screening {timeframe} timeframe...")
                    results = screening_service.screen_altcoins(
                        timeframe=timeframe,
                        min_volume=settings.MIN_VOLUME_USD
                    )

                    # Filter high-score opportunities
                    high_score_results = [
                        r for r in results
                        if r['total_score'] >= 70  # High threshold for alerts
                    ]

                    if high_score_results:
                        all_results.extend(high_score_results)
                        print(f"  Found {len(high_score_results)} high-score opportunities in {timeframe}")

                except Exception as e:
                    print(f"  Error screening {timeframe}: {e}")

            # Send notification if high-score opportunities found
            if all_results:
                try:
                    await notification_service.send_screening_alert(
                        results=all_results,
                        timeframe='multi',
                        send_email=True,
                        send_telegram=True
                    )
                    print(f"  Alert sent for {len(all_results)} opportunities")
                except Exception as e:
                    print(f"  Failed to send alert: {e}")

        print(f"[{datetime.now()}] Screening job completed\n")

    def start_monitoring(self, timeframes: List[str] = None):
        """Start continuous monitoring"""
        self.is_running = True
        print(f"Starting monitoring service (interval: {self.screening_interval}s)...")

        # Schedule periodic screening
        schedule.every(self.screening_interval).seconds.do(
            lambda: asyncio.run(self.run_screening_job(timeframes))
        )

        # Run initial screening immediately
        asyncio.run(self.run_screening_job(timeframes))

        # Keep running
        while self.is_running:
            schedule.run_pending()
            time.sleep(1)

    def stop_monitoring(self):
        """Stop monitoring"""
        self.is_running = False
        print("Monitoring service stopped")


# Standalone monitoring script
if __name__ == "__main__":
    monitor = MonitorService()

    print("""
    ╔═══════════════════════════════════════════════════════╗
    ║     Binance Altcoin Screener - Monitor Service       ║
    ║                                                       ║
    ║  This service continuously monitors altcoins and      ║
    ║  sends alerts when high-score opportunities arise.    ║
    ║                                                       ║
    ║  Press Ctrl+C to stop                                 ║
    ╚═══════════════════════════════════════════════════════╝
    """)

    try:
        monitor.start_monitoring(timeframes=['5m', '15m', '1h'])
    except KeyboardInterrupt:
        print("\n\nShutting down gracefully...")
        monitor.stop_monitoring()
